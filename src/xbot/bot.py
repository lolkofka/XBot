from aiogram import Dispatcher, Router, Bot
from aiogram.enums import ParseMode

from .config import config


class XBot:
    def __init__(self):
        self.router = Router()

        self.dispatcher = Dispatcher()
        self.dispatcher.include_router(self.router)

        self.main_bot = Bot(config['xbot']['token'], parse_mode=ParseMode.HTML)

    async def start(self):
        await self.dispatcher.start_polling(self.main_bot)
