"""
This module contains middleware for sending messages. It is part of the backend application of the sec-microservice-rh project.

The middleware defined here can be used to send messages to other parts of the application or to external services. This can be useful for logging, notifications, or inter-service communication.
"""

import asyncio
from collections.abc import Coroutine
import threading
from typing import Any, Callable

from app.messages.client import AsyncSender, SyncSender


def run_sender(sender: SyncSender, message):
    sender.send_message(message)


async def send_async_message_loop(message: str) -> None:
    print("Creating task...")
    loop = asyncio.get_event_loop()
    sender = AsyncSender(queue_name="pt.#")
    task = loop.create_task(sender.publish(message, loop))
    await task


def send_async_message(message: str) -> None:
    sender = SyncSender(queue_name="pt.#")
    threading.Thread(target=run_sender, args=(sender, message)).start()


def get_async_message_sender() -> Callable[[str], None]:
    return send_async_message


def get_async_message_sender_on_loop() -> Callable[[str], Coroutine[Any, Any, None]]:
    print("Returning function")
    return send_async_message_loop
