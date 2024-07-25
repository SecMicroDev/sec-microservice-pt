"""Base class for async broker connections."""

from asyncio import AbstractEventLoop
from os import environ

import aio_pika


class AsyncBroker:
    # pylint: disable=too-few-public-methods

    def default_connect_robust(self, loop: AbstractEventLoop):
        return aio_pika.connect_robust(
            host=environ.get("BROKER_HOST", "my-rabbit"),
            username=environ.get("BROKER_USER", "guest"),
            password=environ.get("BROKER_PASS", "guest"),
            port=int(environ.get("BROKER_PORT", "5672")),
            loop=loop,
        )
