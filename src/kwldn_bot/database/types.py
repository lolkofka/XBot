from datetime import datetime

from beanie import Document
from pydantic import Field


class BaseUser(Document):
    user_id: int
    username: str | None
    joined: datetime = Field(default_factory=datetime.now)
