import datetime
from typing import Optional

from beanie import Document


class BaseUser(Document):
    user_id: int
    username: Optional[str]
    joined: datetime.datetime
