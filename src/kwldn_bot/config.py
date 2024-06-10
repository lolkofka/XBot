import json
import os.path

from pydantic import BaseModel

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
        if os.path.exists(self.get_pathname()):
            with open(self.get_pathname(), 'r', encoding='utf-8') as f:
                super().__init__(**json.load(f))
        else:
            super().__init__()

        with open(self.get_pathname(), 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, ensure_ascii=True, sort_keys=True, indent=4)

    def get_pathname(self) -> str:
        return 'data/config.json'
