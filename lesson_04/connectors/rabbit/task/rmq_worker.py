from dataclasses import dataclass

import aio_pika
import json


@dataclass
class WorkerClientConfig:
    rabbit_url: str
    queue_name: str


class WorkerClient:
    def __init__(self, config: WorkerClientConfig):
        self.config = config
        self.connection = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def create_connection(self):
        self.connection = await aio_pika.connect(url=self.config.rabbit_url)

    async def put(self, data: dict):
        """
        положить сообщение с телом data в очередь с название WorkerClientConfig.queue_name
        """
        await self.create_connection()
        channel = await self.connection.channel()
        await channel.declare_queue(self.config.queue_name)
        await channel.default_exchange.publish(
            aio_pika.Message(json.dumps(data).encode('utf-8')),
            routing_key=self.config.queue_name)

    async def stop(self):
        """
        закрыть все ресурсы, с помощью которых работали с rabbitmq
        """
        await self.connection.close()


@dataclass
class WorkerConfig:
    rabbit_url: str
    queue_name: str
    capacity: int = 1


class Worker:
    def __init__(self, config: WorkerConfig):
        self.config = config
        self.connection = None

    async def create_connection(self):
        self.connection = await aio_pika.connect(url=self.config.rabbit_url)

    async def handler(self, msg: aio_pika.IncomingMessage):
        """
        метод, который пользователи-программисты должны переопределять в классах наследниках
        """
        pass

    async def _worker(self, msg: aio_pika.IncomingMessage):
        """
        нужно вызвать метод self.handler
        если он завершился корректно, то подтвердить обработку сообщения (ack)
        """
        print('working message')
        async with msg.process():
            await self.handler(msg)
        print('Acked!')

    async def start(self):
        """
        объявить очередь и добавить обработчик к ней
        """
        await self.create_connection()
        channel = await self.connection.channel()
        await channel.set_qos(prefetch_count=self.config.capacity)
        queue = await channel.declare_queue(self.config.queue_name)
        await queue.consume(self._worker)

    async def stop(self):
        """
        закрыть все ресурсы, с помощью которых работали с rabbit
        """
        await self.connection.close()
