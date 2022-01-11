import asyncio


class Resource:
    def __init__(self):
        self._users_count = 0

    async def use(self):
        self._users_count += 1

        if self._users_count > 1:
            await asyncio.sleep(5)
        else:
            await asyncio.sleep(0.1)

        self._users_count -= 1


async def worker(res: Resource, lock: asyncio.Lock):
    """
    Используя lock, гарантировать, что несколько  worker-ов не будут использовать единовременно ресурс
    """
    async with lock:
        await res.use()


async def main():
    lock = asyncio.Lock()
    res = Resource()
    await asyncio.gather(*[worker(res, lock) for _ in range(10)])


asyncio.run(main())
