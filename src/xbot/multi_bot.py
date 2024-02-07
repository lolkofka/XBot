import random
import string
from typing import Optional

from aiogram import Bot, Dispatcher, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.types import User
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, TokenBasedRequestHandler, setup_application
from aiohttp import web

from xbot.config import config

MAIN_BOT_PATH = "/webhook/main"
OTHER_BOTS_PATH = "/webhook/bot/{bot_token}"


class XMultiBot:
    def __init__(self, base_url: str, port: int, startup_tokens: list[str]):
        self.router = Router()

        self._dispatcher = Dispatcher()
        self._dispatcher.include_router(self.router)

        self.minions: dict[str, Bot] = {}

        self._bot_settings = {"session": AiohttpSession(), "parse_mode": ParseMode.HTML}
        self.main_bot = Bot(config['xbot']['token'], **self._bot_settings)

        self._secret = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(64)])
        self._port = port
        self._base_url = base_url

        async def on_startup(bot: Bot):
            for token in startup_tokens:
                new_bot = Bot(token, self.main_bot.session)
                try:
                    await new_bot.get_me()
                except TelegramUnauthorizedError:
                    continue
                await new_bot.delete_webhook(drop_pending_updates=True)
                await new_bot.set_webhook("/webhook/bot/" + token)
                self.minions[token] = new_bot

            await bot.set_webhook(f"{self._base_url}{MAIN_BOT_PATH}", secret_token=self._secret)

        self._dispatcher.startup.register(on_startup)

    async def add_minion(self, token: str) -> Optional[User]:
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

    async def start(self):
        app = web.Application()
        SimpleRequestHandler(dispatcher=self._dispatcher, bot=self.main_bot,
                             secret_token=self._secret).register(app,
                                                                 path=MAIN_BOT_PATH)
        TokenBasedRequestHandler(
            dispatcher=self._dispatcher,
            bot_settings=self._bot_settings
        ).register(app, path=OTHER_BOTS_PATH)

        setup_application(app, self._dispatcher, bot=self.main_bot)

        web.run_app(app, host='0.0.0.0', port=self._port)
