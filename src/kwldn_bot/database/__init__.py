from typing import Type

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from .types import *


async def connect(mongo: str, database: str, models: list[Type[Document]]):
    client = AsyncIOMotorClient(mongo)

    await init_beanie(database=client[database],
                      document_models=models)
