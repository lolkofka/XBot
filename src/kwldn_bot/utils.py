import asyncio
from datetime import datetime
from typing import Union

from aiogram import Bot
from aiogram.exceptions import AiogramError
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_timestamp(time: int) -> str:
    return datetime.fromtimestamp(time + 3600 * 3).strftime("%H:%M %d.%m.%Y")


async def notify(bot: Bot, user_id: int, text: str):
    try:
        await bot.send_message(user_id, text)
    except AiogramError:
        pass


async def distribute(bot: Bot, ids: list[int], text: str, additional_tasks: list[...] | None = None) -> tuple[...]:
    if additional_tasks is None:
        additional_tasks = []

    tasks = additional_tasks
    for user_id in ids:
        tasks.append(notify(bot, user_id, text))
    return await asyncio.gather(*tasks)


async def confirm_action(data: Union[Message, CallbackQuery], description: str, warning: bool,
                         callback_data: str):
    builder = InlineKeyboardBuilder()

    builder.button(text='✅ Подтвердить', callback_data=callback_data)
    builder.button(text='❌ Отмена', callback_data='state_clear')

    if isinstance(data, Message):
        # noinspection PyTypeChecker
        func = data.answer
    else:
        # noinspection PyTypeChecker
        func = data.message.edit_text

    await func(
        f'Вы уверены, что хотите {description}?' + ('\n\n⚠️ Это действие необратимо' if warning else ''),
        reply_markup=builder.as_markup())
