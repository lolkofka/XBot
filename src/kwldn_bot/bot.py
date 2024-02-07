from aiogram import Dispatcher, Router, Bot
from aiogram.enums import ParseMode


class XBot:
    def __init__(self, token: str):
        self.router = Router()

        self.dispatcher = Dispatcher()
        self.dispatcher.include_router(self.router)

        self.main_bot = Bot(token, parse_mode=ParseMode.HTML)

    async def start(self):
        await self.dispatcher.start_polling(self.main_bot)
