from datetime import datetime

from beanie import Document


class BaseUser(Document):
    user_id: int
    username: str | None
    joined: datetime
