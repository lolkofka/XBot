import json
import os.path
from typing import TypeVar

from pydantic import BaseModel

config_file = 'data/config.json'

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

    def __init__(self):
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                super().__init__(**json.load(f))
        else:
            super().__init__()

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, ensure_ascii=True, sort_keys=True, indent=4)


R = TypeVar('R')
