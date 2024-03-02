import collections
import json
import os.path
from typing import TypeVar

from pydantic import BaseModel

config_file = 'data/config.json'


def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


if not os.path.exists('data'):
    os.mkdir('data')


class BotSettings(BaseModel):
    token: str = ''
    owners: list[int] = []
    mongo: str = ''
    debug: bool = True
    database: str = ''


class BasicBotConfig(BaseModel):
    bot: BotSettings = BotSettings()


R = TypeVar('R')


def load_config(config_type: R) -> R:
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            bot_config = config_type(**json.load(f))
    else:
        bot_config = config_type()

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(bot_config.model_dump(), f, ensure_ascii=True, sort_keys=True, indent=4)

    return bot_config
