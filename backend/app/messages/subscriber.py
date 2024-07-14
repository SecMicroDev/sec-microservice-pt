from collections.abc import Coroutine
from os import environ
from typing import Callable
import aio_pika


class AsyncListener:
    def __init__(self, queue_name, processor: Callable[[str], Coroutine[None, None, None]]):
        self.queue_name = queue_name
        self.message_processor = processor


    async def callback(self, message: aio_pika.abc.AbstractIncomingMessage):
        async with message.process():
            await self.message_processor(message.body.decode())

    
    async def iterate_queue(self, queue: aio_pika.abc.AbstractQueue):
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await self.message_processor(message.body.decode())


    async def listen(self, loop):
        connection = await aio_pika.connect_robust(
            host=environ.get("BROKER_HOST", "my-rabbit"),
            username=environ.get("BROKER_USER", "guest"),
            password=environ.get("BROKER_PASS", "guest"),
            port=int(environ.get("BROKER_PORT", "5672")),
            loop=loop,
        )
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            environ.get('DEFAULT_EXCHANGE', 'openferp'),
            type=aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        queue = await channel.declare_queue('rhevent/rh', durable=True)
        await queue.bind(exchange, routing_key=self.queue_name)
        await self.iterate_queue(queue)

        # print(" [*] Waiting for messages. To exit press CTRL+C")
        # await asyncio.Future()  # Run forever
        return connection

    # def run_listener_thread(self):
    #     asyncio.run(self.listen())


# Example usage:
# if __name__ == "__main__":
#     listener = AioPikaListener(queue_name='async_queue')
#     asyncio.run(listener.listen())
