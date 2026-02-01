# Falco Server

An async first http server framework designed to run on microcontroller dev boards. Easily provide an HTML interface to your dev board for diy automation and IoT projects. No multithreading headaches. Easily add mundane tasks to the global event loop to achieve concurrency.

## Features

- Async-first design
- Deterministic startup
- Static route registration
- Static task registration
- No third-party dependencies
- Built-in HTML templating
- HTML form data parsing

## Project Structure

```
project_root/
├── FalcoServer/
│   ├── static/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── script.js
│   │   └── style.css
│   ├── __init__.py
│   ├── background_task.py
│   ├── dns.py
│   ├── server.py
│   └── template.py
├── boot.py
├── main.py
└── README.md
```

## Installation

### Prerquisites

- MicroPython version 1.24 or higher

### Clone or Download Repository

[Download](https://github.com/OCLAFLOPTSON/falcoserver/archive/refs/heads/main.zip "Direct Download")

#### Clone

```bash
git clone https://github.com/OCLAFLOPTSON/falcoserver.git
```

## Example Usage

```python
from FalcoServer import (
    Request, Response, CreateRoute, BackgroundTask,
    render_template, run_server
)

@BackgroundTask.run_loop()
async def arbitrary_task():
    ...

@CreateRoute.get('/')
async def index(request: Request):
    return render_template(
        '/FalcoServer/static/index.html',
        title="Index"
    )

@CreateRoute.get('/stop/task')
async def stop_task(request: Request):
    arbitrary_task.stop()
    return Response('Stopped arbitrary task.')

run_server()
```