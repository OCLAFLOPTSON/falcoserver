"""
Falco Server v - 0.0.3

An async first http server framework designed to run on microcontroller
dev boards capable of running MicroPython.

Easily provide an HTML interface to your dev board for diy automation and
IoT projects.

No multithreading headaches. Easily add mundane tasks to the global event
loop to achieve concurrency.

MIT License

Copyright (c) 2026 Timothy S Falco

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files
(the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice (including the next
paragraph) shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
THE USE OR OTHER DEALINGS IN THE SOFTWARE


"""

__version__ = "0.0.3"

class FileNotFound(Exception):
    '''File not found error'''
    def __init__(self, path: str):
        super().__init__(f'File "{path}" not found.')

import gc
gc.threshold(16000)

from FalcoServer.server import (
    Route, Response, Request, CreateRoute, Server,
    settings,
    run_server
)
from FalcoServer.template import render_template
from FalcoServer.background_task import (
    BackgroundTask, InteractiveTask
)