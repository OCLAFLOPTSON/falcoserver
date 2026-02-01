from sys import print_exception
from uasyncio import get_event_loop, sleep

interactive_tasks = dict()

class CoroutineObject:
    ...

class InteractiveTask:
    '''Creates an interactive background task.'''
    def __init__(self, name: str, coroutine: CoroutineObject,
                 interval):
        self.name = name
        self._stop = False
        self.coroutine = coroutine
        self.interval = interval
    
    def stop(self):
        '''Performs an interupt sequence to stop the running coroutine
        loop.'''
        async def _intrpt():
            self._stop = True
            await sleep(0.25)
            self._stop = False
        get_event_loop().create_task(_intrpt())

    def run_loop(self):
        '''Repeats the task coroutine until an interupt is flagged.'''
        try:
            async def loop(self):
                while not self._stop:
                    await self.coroutine()
                    await sleep(self.interval)
            get_event_loop().create_task(loop(self))
        except Exception as e:
            print_exception(e)
    
    def run(self):
        '''Runs the task coroutine once.'''
        async def coro():
            await self.coroutine
        get_event_loop().create_task(coro())

class BackgroundTask:
    '''Library for deploying and interacting with background tasks.'''

    @staticmethod
    def create():
        '''Creates an InteractiveTask object and adds it to the global
        interactive_tasks dict.'''
        def deco(func):
            global interactive_tasks
            print(f"Created Background Task: {func.__name__}")
            it = InteractiveTask(
                func.__name__,
                func
            )
            interactive_tasks[func.__name__] = it
            return func
        return deco

    @staticmethod
    def run_loop(interval: float=0.025):
        '''Creates an InteractiveTask object and adds it to the running
        event loop.'''
        def deco(func):
            try:
                print(f"Starting Background Task: {func.__name__}")
                interactive_tasks[func.__name__] = InteractiveTask(
                    func.__name__,
                    func,
                    interval
                )
                interactive_tasks[func.__name__].run_loop()
                return interactive_tasks[func.__name__]
            except Exception as e:
                print_exception(e)
        return deco
    
    @staticmethod
    def run_basic():
        '''Add the decorated coroutine to the running event loop
        without creating an InteractiveTask object.'''
        def deco(func):
            async def _task(func):
                print(f"Starting Background Task: {func.__name__}")
                await func()
            get_event_loop().create_task(_task(func))
            return func
        return deco
    