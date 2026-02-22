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
        self.running = False
        self._stop = False
        self.coroutine = coroutine
        self.interval = interval
    
    def stop(self):
        '''Performs an interupt sequence to stop the running coroutine
        loop.'''
        async def _intrpt():
            self._stop = True
            await sleep(self.interval+1)
            self._stop = False
        get_event_loop().create_task(_intrpt())

    def run_loop(self):
        '''Repeats the task coroutine until an interupt is flagged.'''
        try:
            async def loop(self):
                self.running = True
                try:
                    while not self._stop:
                        await self.coroutine()
                        await sleep(self.interval)
                finally:
                    self.running = False
            get_event_loop().create_task(loop(self))
        except Exception as e:
            print_exception(e)
    
    def run(self):
        '''Runs the task coroutine once.'''
        async def coro():
            await self.coroutine
        get_event_loop().create_task(coro())

class BackgroundTask:
    '''Library for deploying and interacting with background tasks.\n
    # API
    - ## .create() 
        Creates an InteractiveTask object and adds it to the global dict.
    - ## .run_basic() 
        Add the decorated coroutine to the running event loop without 
        creating an InteractiveTask object.
    - ## .run_loop() 
        Creates an InteractiveTask object and adds it to the running
        event loop.
    # InteractiveTask Hooks
    - ## .run()
        Run the coroutine once.
    - ## .run_loop()
        Wraps the coroutine in a loop that runs until an interrupt call.
    - ## .stop()
        Performs an interrupt sequence to stop the InteractiveTask.
    # Example
    ```python
    @BackgroundTask.create()
    async def arbitrary_task():
        ...
    
    arbitrary_task.run_loop()
    arbitrary_task.stop()
    ```
    '''

    @staticmethod
    def create(interval: float=0.025) -> InteractiveTask:
        '''Creates an InteractiveTask object and adds it to the global
        interactive_tasks dict.'''
        def deco(func):
            global interactive_tasks
            print(f"Created Background Task: {func.__name__}")
            interactive_tasks[func.__name__] = InteractiveTask(
                func.__name__,
                func,
                interval
            )
            return interactive_tasks[func.__name__]
        return deco

    @staticmethod
    def run_loop(interval: float=0.025) -> InteractiveTask:
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
    