from sys import print_exception
from network import WLAN, AP_IF
from uasyncio import (
    StreamReader, StreamWriter,
    run, get_event_loop, sleep, create_task,
    start_server
)
from FalcoServer.uSettings import settings, SettingType
from FalcoServer.dns import dns_server

def _char_check(char, string):
    if len(char):
        if char[0] in string:
            return True
    return False

#######################################~Class~Declarations~##############

class Request:
    __slots__ = ("method", "path", "path_parts", "headers", "form_data")
    def __init__(self, method, path: str):
        self.method = method
        self.path = path
        self.path_parts = path.strip("/").split("/") if path != "/" else ['']
        self.headers = dict()
        self.query_params = dict()
        self.form_data = dict()
        if _char_check("?", path):
            ps = path.split("?")
            self.path = ps[0]
            params = ps[1]
            if _char_check("&", params):
                params = params.split("&")
                for param in params:
                    if _char_check("=", params):
                        p = param.split("=")
                        self.form_data[p[0]] = p[1]
            else:
                if _char_check("=", params):
                    params = params.split("=")
                    self.form_data[params[0]] = params[1]
        self.content_type = ""

class Response:
    __slots__ = ("status", "headers", "body", "form_data")
    def __init__(self, body="", status=200, headers={}):
        self.status = status
        self.body = body
        self.headers = headers
        self.form_data = dict()
    
    def __repr__(self):
        return f"<~Route STATUS({self.status}) HEADERS({self.headers})~>"

class Route:
    __slots__ = ("path", "methods", "handler", "parts", "priority")
    def __init__(self, path, handler, methods, priority):
        self.path = path
        self.handler = handler
        self.methods = methods
        self.parts = path.strip("/").split("/") if path != "*" else ["*"]
        self.priority = priority

    def matches(self, req: Request):
        if self.path == "*":
            return True
        if len(self.parts) != len(req.path_parts):
            return False
        if self.path != req.path:
            return False
        return True

class Router:
    def __init__(self):
        self._routes = []
        self._locked = False

    def add(self, path, handler, methods=("GET",), priority=0):
        if self._locked:
            raise RuntimeError("Routes locked after startup")
        self._routes.append(Route(path, handler, methods, priority))

    def build(self):
        self._routes.sort(
            key=lambda r: (r.priority, len(r.parts)),
            reverse=True
        )
        self._locked = True

    def resolve(self, request):
        for route in self._routes:
            if (request.method in route.methods and route.matches(request)):
                return route.handler
        return None

router = Router()

class CreateRoute:
    """Decorators for declaring routes."""
    @staticmethod
    def get(path, priority=0):
        def deco(fn):
            router.add(path, fn, ("GET",), priority)
            return fn
        return deco

    @staticmethod
    def post(path, priority=0):
        def deco(fn):
            router.add(path, fn, ("POST",), priority)
            return fn
        return deco

####################################~Function~Declarations~##############

def parse_form(body: bytes) -> dict:
    form_data = dict()
    for pair in body.split(b"&"):
        if b"=" not in pair:
            continue
        k, v = pair.split(b"=", 1)
        form_data[k.decode()] = v.decode()
    return form_data

async def read_request(reader: StreamReader) -> Request:
    line = await reader.readline()
    if not line:
        return None

    method, path, _ = line.decode().split(" ")
    req = Request(method, path)

    while True:
        h = await reader.readline()
        if h in (b"\r\n", b"\n", b""):
            break
        k, v = h.decode().split(":", 1)
        req.headers[k.strip()] = v.strip()
    
    _length = int(req.headers.get("Content-Length", 0))
    if _length:
        raw_body = await reader.readexactly(_length)
        req.content_type = req.headers.get("Content-Type")
        if req.content_type.startswith("application/x-www-form-urlencoded"):
            req.form_data = parse_form(raw_body)

    return req

async def send_response(writer, response: Response):
    try:
        writer.write(
            "HTTP/1.1 {} OK\r\n".format(response).encode()
        )
        for k, v in response.headers.items():
            writer.write("{}: {}\r\n".format(k, v).encode())
        writer.write(b"\r\n")
        if type(response.body).__name__ == 'generator':
            for chunk in response.body:
                writer.write(chunk)
        else:
            writer.write(response.body)
        await writer.drain()
        return
    except Exception as e:
        print_exception(e)

def redirect(path: str):
    try:
        send_response(
            StreamWriter,
            Response(status=303, headers={"Location":path})
        )
    except Exception as e:
        print_exception(e)

async def reload_after(writer, request: Request):
    ''' Reloads the current page after performing some action.
        Defaults to "/".'''
    ref  = request.headers.get("referer", "/")
    response = Response(status=303, headers={"Location":ref})
    await send_response(writer, response)
    
async def handle_http_client(reader: StreamReader, writer: StreamWriter):
    try:
        req = await read_request(reader)
        if not req:
            return
        
        peer = writer.get_extra_info("peername")
        if peer:
            client_ip, client_port = peer
        print(f"Call From -> client ip: {client_ip} port: {client_port}")
        
        handler = router.resolve(req)
        
        if not handler:
            resp = Response("Not Found", 404)
            print(f"/{req.path} | {req.method} | {resp.status}")
        else:
            resp = await handler(req)
            print(f"/{req.path} | {req.method} | {resp.status}")

        await send_response(writer, resp)
    except Exception as e:
        print_exception(e)
    finally:
        await writer.wait_closed()

####################################~Program Loop~#######################

def start_ap() -> str:
    """Start Access Point. Returns AP IP Address"""
    print("Starting Access Point...")
    ap = WLAN(AP_IF)
    ap.active(True)
    ap.config(
        essid=settings.get(SettingType.ssid),
        security=0
    )
    while not ap.active():
        pass
    return ap.ifconfig()[0]


async def main():
    from FalcoServer.uSettings import settings
    local_ip = start_ap()
    create_task(_http_server(local_ip))
    create_task(dns_server(local_ip))
    while True:
        await sleep(3600)

async def _http_server(local_ip):
    router.build()
    server = await start_server(
        handle_http_client, "0.0.0.0", 80, backlog=2
    )
    print(f'Server Started on IP: {local_ip}')
    print("Thank you for using Falco Server!")
    print(f'Application Running @: http://{settings.get(SettingType.domain)}/')
    async with server:
        get_event_loop().run_forever()
        await server.wait_closed()

def run_server() -> None:
    '''Wrapper for uasyncio.run(main())'''
    run(main())