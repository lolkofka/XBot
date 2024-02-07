from datetime import datetime
from typing import Union

from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_timestamp(time: int) -> str:
    return datetime.fromtimestamp(time + 3600 * 3).strftime("%d.%m.%Y %H:%M")


async def confirm_action(data: Union[Message, CallbackQuery], description: str, warning: bool,
                         callback_data: str):
    builder = InlineKeyboardBuilder()

    builder.button(text='✅ Подтвердить', callback_data=callback_data)
    builder.button(text='❌ Отмена', callback_data='state_clear')

    if type(data) is Message:
        func = data.answer
    else:
        func = data.message.edit_text

    await func(
        f'Вы уверены, что хотите {description}?' + ('\n\n⚠️ Это действие необратимо' if warning else ''),
        reply_markup=builder.as_markup())
