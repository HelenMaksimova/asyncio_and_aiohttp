import asyncio
from typing import Optional

from clients.tg.api import TgClient


class FabricClient:
    types = {
        'tg': TgClient
    }

    @classmethod
    def create(cls, type_):
        try:
            client_cls = cls.types[type_]
            return client_cls
        except KeyError:
            raise ValueError(f'Client type {type_} is undefined')


class Poller:

    CLIENT_TYPE = 'tg'

    def __init__(self, token: str, queue: asyncio.Queue):
        # обязательный параметр, в _task нужно положить запущенную корутину поллера
        self._task: Optional[asyncio.Task] = None
        self.token = token
        self.queue = queue
        self.client = FabricClient.create(self.CLIENT_TYPE)
        self.is_running = False

    async def _worker(self):
        """
        нужно получать данные из tg, стоит использовать метод get_updates_in_objects
        полученные сообщения нужно положить в очередь queue
        в очередь queue нужно класть UpdateObj
        """
        update_data = None
        try:
            async with self.client(self.token) as client:
                offset = 0
                while self.is_running:
                    update_data = await client.get_updates_in_objects(timeout=60, offset=offset)
                    if update_data:
                        offset = update_data[-1].update_id + 1
                        for item in update_data:
                            await self.queue.put(item)
                        update_data = None
        except asyncio.CancelledError:
            if update_data:
                for item in update_data:
                    await self.queue.put(item)

    def start(self):
        """
        нужно запустить корутину _worker
        """
        self.is_running = True
        self._task = asyncio.create_task(self._worker())

    async def stop(self):
        """
        нужно отменить корутину _worker и дождаться ее отмены
        """
        self.is_running = False
        self._task.cancel()
        await asyncio.gather(self._task)


if __name__ == '__main__':

    start_queue = asyncio.Queue()
    poller = Poller('', start_queue)


    async def main():
        poller.start()
        await asyncio.sleep(10)
        await poller.stop()


    asyncio.run(main())
