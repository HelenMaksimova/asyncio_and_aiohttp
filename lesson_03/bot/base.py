import asyncio
from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

from bot.poller import Poller
from bot.worker import Worker, WorkerConfig


@dataclass
class BotConfig:
    token: str
    worker: WorkerConfig


class Bot:
    def __init__(self, config: BotConfig):
        queue = asyncio.Queue()
        self.poller = Poller(config.token, queue)
        self.worker = Worker(config.token, queue, config.worker)

    async def start(self):
        self.poller.start()
        self.worker.start()

    async def stop(self):
        await self.poller.stop()
        await self.worker.stop()


if __name__ == '__main__':

    load_dotenv()

    worker_config = WorkerConfig('', '', '', '')
    config = BotConfig(getenv('BOT_TOKEN'), worker_config)


    async def main():
        bot = Bot(config)
        await bot.start()
        await asyncio.sleep(1)
        await bot.stop()

    asyncio.run(main())
