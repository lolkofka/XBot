import asyncio
import random
import string
from typing import Dict, Optional

from aiogram import Dispatcher, Router, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.types import User, Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application, TokenBasedRequestHandler
from aiohttp import web


MAIN_BOT_PATH = "/webhook/main"
OTHER_BOTS_PATH = "/webhook/bot/{bot_token}"


class BaseBot:
    def __init__(self, token: str):
        self.token = token
        self.router = Router()
        self.dispatcher = Dispatcher()
        self.dispatcher.include_router(self.router)
        self._bot_settings = {
            "session": AiohttpSession(),
            "default": DefaultBotProperties(parse_mode=ParseMode.HTML),
        }
        self.main_bot = Bot(self.token, **self._bot_settings)

    async def start(self) -> None:
        pass


class XBot(BaseBot):
    def __init__(self, token: str):
        super().__init__(token)

    async def start(self) -> None:
        await self.dispatcher.start_polling(self.main_bot)


class XMultiBot(BaseBot):
    def __init__(self, main_token: str, base_url: str = None, port: int = None, use_webhook: bool = False):
        super().__init__(main_token)
        self.use_webhook = use_webhook
        self._base_url = base_url
        self._port = port
        self._secret = "".join([random.choice(string.ascii_letters + string.digits) for _ in range(64)])
        self._startup_tokens: list[str] = []
        self._running = False

        self.minions: Dict[str, Bot] = {}
        self._polling_tasks: Dict[int, asyncio.Task] = {}

        self.app: Optional[web.Application] = web.Application() if self.use_webhook else None
        if self.use_webhook:
            SimpleRequestHandler(
                dispatcher=self.dispatcher,
                bot=self.main_bot,
                secret_token=self._secret
            ).register(self.app, path=MAIN_BOT_PATH)
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
                    await new_bot.set_webhook(f"{self._base_url}/webhook/bot/{token}")
                    self.minions[token] = new_bot
                await bot.set_webhook(f"{self._base_url}{MAIN_BOT_PATH}", secret_token=self._secret)

            self.dispatcher.startup.register(on_startup)

    async def add_minion(self, token: str) -> Optional[User]:
        new_bot = Bot(token, **self._bot_settings)
        try:
            bot_user = await new_bot.get_me()
        except TelegramUnauthorizedError:
            return None
        if self.use_webhook:
            await new_bot.delete_webhook(drop_pending_updates=True)
            await new_bot.set_webhook(f"{self._base_url}{OTHER_BOTS_PATH.format(bot_token=token)}")
            self.minions[token] = new_bot
            return bot_user
        await new_bot.delete_webhook(drop_pending_updates=True)
        self.minions[token] = new_bot
        if self._running:
            await self._start_single_polling(new_bot)
        return bot_user

    async def delete_minion(self, token: str) -> bool:
        bot = self.minions.get(token)
        if not bot:
            return False
        if self.use_webhook:
            try:
                await bot.delete_webhook()
            except Exception:
                pass
            del self.minions[token]
            return True
        task = self._polling_tasks.pop(bot.id, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        del self.minions[token]
        return True

    def register_minions(self, tokens: list[str]):
        if self.use_webhook:
            self._startup_tokens = tokens
        else:
            self._startup_tokens = tokens

    async def _start_webhook_server(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self._port)
        await site.start()
        await asyncio.Event().wait()

    async def _polling_loop(self, bot: Bot):
        offset = 0
        while True:
            try:
                updates = await bot.get_updates(offset=offset, timeout=30)
                if updates:
                    for u in updates:
                        await self.dispatcher.feed_update(bot, Update.model_validate(u))
                        offset = u.update_id + 1
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1)

    async def _start_single_polling(self, bot: Bot):
        await bot.get_me()
        await bot.delete_webhook(drop_pending_updates=True)
        task = asyncio.create_task(self._polling_loop(bot))
        self._polling_tasks[bot.id] = task

    async def _start_polling_all(self):
        await self.main_bot.get_me()
        await self.main_bot.delete_webhook(drop_pending_updates=True)
        for token in self._startup_tokens:
            if token in self.minions:
                continue
            b = Bot(token, **self._bot_settings)
            try:
                await b.get_me()
            except TelegramUnauthorizedError:
                continue
            await b.delete_webhook(drop_pending_updates=True)
            self.minions[token] = b
        self._running = True
        await self._start_single_polling(self.main_bot)
        for b in self.minions.values():
            await self._start_single_polling(b)
        await asyncio.gather(*self._polling_tasks.values())

    async def start(self):
        if self.use_webhook:
            await self._start_webhook_server()
        else:
            await self._start_polling_all()
