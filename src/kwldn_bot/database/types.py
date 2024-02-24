import datetime
from typing import Optional

from pydantic import BaseModel


class BaseUser(BaseModel):
    user_id: int
    username: Optional[str]
    joined: datetime.datetime
