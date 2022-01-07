import asyncio
import typing
from asyncio import Event


class Resource:
    def __init__(self):
        self.val = 0


async def set_event(event: Event):
    await asyncio.sleep(1)
    event.set()

    while True:
        await asyncio.sleep(10)


async def worker(r: Resource):
    await asyncio.sleep(0.5)
    r.val += 1

    while True:
        await asyncio.sleep(10)


async def do_until_event(coros: list[typing.Coroutine], event: asyncio.Event):
    """Функция должна обрабатывать Task|Coroutine|Future объекты до тех пор, пока не будет вызван метод Event.set() """
    loop = asyncio.get_event_loop()
    tasks = []
    for coro in coros:
        tasks.append(asyncio.create_task(coro))
    await event.wait()

    for task in tasks:
        task.cancel()


async def main():
    res = Resource()
    event = asyncio.Event()
    coros = [worker(res) for _ in range(10)]
    coros.append(set_event(event))
    await do_until_event(coros, event)


asyncio.run(main())
