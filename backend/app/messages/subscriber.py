"""
This module contains the AsyncListener class which is used to asynchronously 
listen to a message queue.

Class AsyncListener:
    This class is used to asynchronously listen to a message queue. It inherits 
    from AsyncBroker.

    Attributes:
    - queue_name: The name of the queue to which messages will be sent.
    - message_processor: A callable that processes the messages.

    Methods:
    - callback: Processes a message using the message_processor.
    - iterate_queue: Iterates over the messages in the queue and processes them using 
      the message_processor.
    - listen: Connects to the message broker, declares the exchange and queue, 
      binds the queue to the exchange, and starts iterating over the queue.
"""

from collections.abc import Coroutine
from os import environ
from typing import Callable

import aio_pika
from app.messages.async_broker import AsyncBroker


class AsyncListener(AsyncBroker):
    def __init__(
        self, queue_name, processor: Callable[[str], Coroutine[None, None, None]]
    ):
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
        connection = await self.default_connect_robust(loop)
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            environ.get("DEFAULT_EXCHANGE", "openferp"),
            type=aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        queue = await channel.declare_queue("rhevent/rh", durable=True)
        await queue.bind(exchange, routing_key=self.queue_name)
        await self.iterate_queue(queue)

        return connection
