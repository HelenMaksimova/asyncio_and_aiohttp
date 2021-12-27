import asyncio

import pytest

pytestmark = pytest.mark.asyncio

counter = 0


# TODO используя Semaphore избежать длительного сна
async def do_request(sem):
    global counter
    async with sem:
        counter += 1
        if counter > 5:
            await asyncio.sleep(10)
        await asyncio.sleep(0.1)
        counter -= 1


async def test():
    sem = asyncio.Semaphore(5)
    await asyncio.wait_for(
        asyncio.gather(*[do_request(sem) for _ in range(10)]),
        timeout=1.2,
    )
    print('Done')
