import asyncio
import random
import string

from aiogram import Dispatcher, Router, Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.types import User
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application, TokenBasedRequestHandler
from aiohttp import web


class BaseBot:
    def __init__(self, token: str):
        self.token = token

        self.router = Router()
        self.dispatcher = Dispatcher()
        self.dispatcher.include_router(self.router)

        self._bot_settings = {"session": AiohttpSession(), "parse_mode": ParseMode.HTML}
        self.main_bot = Bot(self.token, **self._bot_settings)

    async def start(self) -> None:
        pass


class XBot(BaseBot):
    def __init__(self, token: str):
        super().__init__(token)

    async def start(self) -> None:
        await self.dispatcher.start_polling(self.main_bot)


MAIN_BOT_PATH = "/webhook/main"
OTHER_BOTS_PATH = "/webhook/bot/{bot_token}"


class XMultiBot(BaseBot):
    def __init__(self, main_token: str, base_url: str, port: int):
        super().__init__(main_token)
        self.minions: dict[str, Bot] = {}

        self._secret = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(64)])
        self._port = port
        self._base_url = base_url
        self._startup_tokens = []

        self.app = web.Application()
        SimpleRequestHandler(dispatcher=self.dispatcher, bot=self.main_bot,
                             secret_token=self._secret).register(self.app,
                                                                 path=MAIN_BOT_PATH)
        TokenBasedRequestHandler(
            dispatcher=self.dispatcher,
            bot_settings=self._bot_settings
        ).register(self.app, path=OTHER_BOTS_PATH)

        setup_application(self.app, self.dispatcher, bot=self.main_bot)

        async def on_startup(bot: Bot):
            for token in self._startup_tokens:
                new_bot = Bot(token, self.main_bot.session)
                try:
                    await new_bot.get_me()
                except TelegramUnauthorizedError:
                    continue
                await new_bot.delete_webhook(drop_pending_updates=True)
                await new_bot.set_webhook("/webhook/bot/" + token)
                self.minions[token] = new_bot

            await bot.set_webhook(f"{self._base_url}{MAIN_BOT_PATH}", secret_token=self._secret)

        self.dispatcher.startup.register(on_startup)

    async def add_minion(self, token: str) -> User | None:
        new_bot = Bot(token, **self._bot_settings)
        try:
            bot_user = await new_bot.get_me()
        except TelegramUnauthorizedError:
            return None
        await new_bot.delete_webhook(drop_pending_updates=True)
        await new_bot.set_webhook(f'{self._base_url}{OTHER_BOTS_PATH.format(bot_token=token)}')
        self.minions[token] = new_bot

        return bot_user

    async def delete_minion(self, token: str) -> bool:
        if token in self.minions:
            await self.minions[token].delete_webhook()
            del self.minions[token]
            return True
        else:
            return False

    def register_minions(self, tokens: list[str]):
        self._startup_tokens = tokens

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, '0.0.0.0', self._port)
        await site.start()
        await asyncio.Event().wait()
