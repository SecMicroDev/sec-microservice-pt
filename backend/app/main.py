"""Main module for the FastAPI application.

This module initializes the FastAPI application, database, and includes all the routes.
It also sets up CORS (Cross-Origin Resource Sharing) to allow requests from specified origins.

Functions:
    create_db(): Initializes the database by creating all tables.

Imports:
    FastAPI: Class to create a new FastAPI instance.
    CORSMiddleware: Middleware for managing CORS.
    create_db: Function to initialize the database.
    router: FastAPI router containing all application routes.
"""

import asyncio
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.messages.subscriber import AsyncListener
from app.messages.event import UpdateEvent

from .db.conn import create_db
from .db.settings import ENV
from app.router.liveness import router as liveness_router
from app.router.products import router as products_router


create_db()


external_update_listener = AsyncListener(
    "external.rh_event", UpdateEvent.process_message
)


@asynccontextmanager
async def listener_span(fapi_app: FastAPI, *args, **kwargs):
    # pylint: disable=unused-argument

    loop = asyncio.get_running_loop()
    task = loop.create_task(external_update_listener.listen(loop))
    yield
    await task
    print("Ending test_span after req")


app = FastAPI()
app.include_router(liveness_router)
app.include_router(products_router)

app.router.lifespan_context = listener_span

# CORS configuration
origins = [
    "http://local.adrianlopes-swe.com.br",  # Adjust this as needed
    "http://app.adrianlopes-swe.com.br",  # Adjust this as needed
]

if ENV == "test":
    origins = [
        *origins,
        "http://localhost:9080",  # Adjust this as needed
        "http://localhost:8080",  # Adjust this as needed
        "http://localhost:3000",  # Adjust this as needed
        "http://localhost:8000",  # Adjust this as needed
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
