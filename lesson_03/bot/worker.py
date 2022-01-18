import asyncio
from dataclasses import dataclass
from typing import List

from clients.fapi.s3 import S3Client
from clients.tg.api import TgClient
from clients.tg.dcs import UpdateObj


@dataclass
class WorkerConfig:
    endpoint_url: str
    aws_secret_access_key: str
    aws_access_key_id: str
    bucket: str
    concurrent_workers: int = 1


class Worker:
    def __init__(self, token: str, queue: asyncio.Queue, config: WorkerConfig):
        # обязательный параметр, в него нужно сохранить запущенные корутины воркера
        self.token = token
        self.queue = queue
        self._tasks: List[asyncio.Task] = []
        # обязательный параметр, выполнять работу с s3 нужно через объект класса self.s3
        # для загрузки файла нужно использовать функцию fetch_and_upload или stream_upload
        self.s3 = S3Client(
            endpoint_url=config.endpoint_url,
            aws_secret_access_key=config.aws_secret_access_key,
            aws_access_key_id=config.aws_access_key_id
        )
        self.is_running = False
        self.config = config

    async def handle_update(self, upd: UpdateObj):
        """
        в этом методе должна происходить обработка сообщений и реализация бизнес-логики
        бизнес-логика бота тестируется с помощью этого метода, файл с тестами tests.bot.test_worker::TestHandler
        """
        chat_id = upd.message.chat.id
        print(upd)
        if upd.message.text == '/start':
            message = '[greetings]'
        elif upd.message.document:
            message = '[document]'
        else:
            message = '[document is required]'
        async with TgClient(self.token) as client:
            await client.send_message(chat_id, message)

    async def _worker(self):
        """
        должен получать сообщения из очереди и вызывать handle_update
        """
        try:
            while self.is_running:
                item = await self.queue.get()
                await self.handle_update(item)
        except asyncio.CancelledError:
            pass

    def start(self):
        """
        должен запустить столько воркеров, сколько указано в config.concurrent_workers
        запущенные задачи нужно положить в _tasks
        """
        self.is_running = True
        self._tasks.extend([asyncio.create_task(self._worker()) for _ in range(self.config.concurrent_workers)])

    async def stop(self):
        """
        нужно дождаться пока очередь не станет пустой (метод join у очереди), а потом отменить все воркеры
        """
        await self.queue.join()
        self.is_running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks)
