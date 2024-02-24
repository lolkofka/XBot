from typing import Type

from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from .types import *
from .. import BasicBotConfig


async def connect(config: BasicBotConfig, models: list[Type[Document]]):
    client = AsyncIOMotorClient(config.bot.mongo)

    await init_beanie(database=client[config.bot.database],
                      document_models=models)
