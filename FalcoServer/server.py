from sys import print_exception
from network import WLAN, AP_IF
from uasyncio import (
    StreamReader, StreamWriter,
    run, get_event_loop, sleep, create_task,
    start_server
)
from FalcoServer.uSettings import settings
from FalcoServer.dns import dns_server

def _char_check(char, string):
    if len(char):
        if char[0] in string:
            return True
    return False

#######################################~Class~Declarations~##############

class Awaitable:
    '''An async function/method or generator'''
    def __await__():
        yield

class Request:
    __slots__ = ("method", "path", "path_parts", "headers", "form_data")
    def __init__(self, method, path: str, local_ip, client_ip):
        self.local_ip = local_ip
        self.client_ip = client_ip
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
    
class Server:
    '''Construct a server object for use in the main loop.
    
        ### security 
            Expects an awaitable which returns a boolean. Return 
            value should be truthy on security check pass, falsey otherwise.
            A falsey return value will result in the rejection of an incoming
            request. \n
            The Request object is injected as an argument and must be
            handled.
    '''
    def __init__(self, security: Awaitable | None=None,
                 router: Router=router, host:str='0.0.0.0', port=80,
                 backlog=2):
        self.security = security
        self.ip = 'unset ip'
        self.router = router
        self.host = host
        self.port = port
        self.backlog = backlog
    
    async def startup(self):
        self.router.build()
        server = await start_server(
            self.http_handler,
            host=self.host,
            port=self.port,
            backlog=self.backlog
        )
        print(f'Server Started on IP: {self.ip}')
        print("Thank you for using Falco Server!")
        print(f'Application Running @: http://{settings.get('domain')}/')
        async with server:
            get_event_loop().run_forever()
            await server.wait_closed()

    async def read_request(self, reader, client_ip) -> Request:
        line = await reader.readline()
        if not line:
            return None

        method, path, _ = line.decode().split(" ")
        req = Request(method, path, self.ip, client_ip)

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
    
    async def http_handler(self, reader: StreamReader, writer: StreamWriter):
        try:
            peer = writer.get_extra_info("peername")
            if peer:
                client_ip, client_port = peer

            request = await self.read_request(reader, client_ip)
            if not request:
                return
            
            if not self.security:
                pass
            else:
                try:
                    if not await self.security(request):
                        return
                except TypeError:
                    raise TypeError('Security protocol must be awaitable.')
            print(f"Call From -> client ip: {client_ip} port: {client_port}")
            
            handler = router.resolve(request)
            
            if not handler:
                resp = Response("Not Found", 404)
                print(f"/{request.path} | {request.method} | {resp.status}")
            else:
                resp = await handler(request)
                print(f"/{request.path} | {request.method} | {resp.status}")

            await send_response(writer, resp)
        except Exception as e:
            print_exception(e)
        finally:
            await writer.wait_closed()

####################################~Function~Declarations~##############

def parse_form(body: bytes) -> dict:
    form_data = dict()
    for pair in body.split(b"&"):
        if b"=" not in pair:
            continue
        k, v = pair.split(b"=", 1)
        form_data[k.decode()] = v.decode()
    return form_data

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

####################################~Program Loop~#######################

def start_ap() -> str:
    """Start Access Point. Returns AP IP Address"""
    print("Starting Access Point...")
    ap = WLAN(AP_IF)
    ap.active(True)
    ap.config(
        essid=settings.get('ssid'),
        security=0
    )
    while not ap.active():
        pass
    return ap.ifconfig()[0]

async def main(server: Server):
    local_ip = start_ap()
    server.ip = local_ip
    create_task(server.startup())
    create_task(dns_server(local_ip))
    while True:
        await sleep(3600)

def run_server(server: Server=Server()) -> None:
    '''Wrapper for uasyncio.run(main())'''
    run(main(server=server))