# This is an example implementation

from asyncio import sleep
from random import randint
from machine import Pin

from FalcoServer import (
    Request, Response, CreateRoute, BackgroundTask, Server,
    render_template, run_server
)

# Background Tasks

@BackgroundTask.create()
async def knight_that_says_ni():
    # Creates an InteractiveTask object using the decorated coroutine.
    # The InteractiveTask instance is reachable by referencing the
    # coroutine without calling it. 
    # Example: knight_that_says_ni.run(), .run_loop(), .stop()
    print("Ni!")
    await sleep(randint(0,4))

# Setting up a simple reed switch sensor
door_contact = Pin(1, Pin.IN, Pin.PULL_UP)
door_open = False

@BackgroundTask.run_loop()
async def door_listener():
    # Loops automatically
    global door_open
    # door_open becomes True when the circuit is completed
    if door_contact.value():
        door_open = True
    else:
        door_open = False

# Routes
@CreateRoute.get('/')
async def index(request: Request):
    return render_template(
        '/FalcoServer/static/index.html',
        title="Home"
    )

@CreateRoute.get('/knight')
async def knight(request: Request):
    if knight_that_says_ni.running:
        knight_that_says_ni.stop()
        return Response("Knight deactivated!")
    knight_that_says_ni.run_loop()
    return Response("Knight activated!")

@CreateRoute.get('/door')
async def door(request: Request):
    if door_open:
        return Response("Door is open!")
    return Response("Door is closed!")

# A custom Server object can optionally be passed to run_server
server = Server(
    host='0.0.0.0',
    port=80
)

# Call run_server after all routes have been declared
run_server(server)