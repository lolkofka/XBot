import collections
import json
import logging
import os.path
from typing import Type

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
    token: str
    owners: list[int]
    mongo: str
    debug: bool
    database: str


class BasicBotConfig(BaseModel):
    bot: BotSettings


def load_config(config_type: Type[BasicBotConfig], default_values: dict[str, ...]):
    config_values = {
        'bot': {
            'token': '',
            'owners': [],
            'mongo': '',
            'debug': False,
            'database': ''
        }
    }
    config_values = update(config_values, default_values)
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            config_values = update(config_values, user_config)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_values, f, ensure_ascii=True, sort_keys=True, indent=4)
    else:
        logging.error('Config was created, restart needed')
        exit(0)
    return config_type(**config_values)
