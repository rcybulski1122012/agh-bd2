import datetime
from typing import Optional

from bunnet import Document
from bunnet import Indexed
from bunnet import PydanticObjectId
from flask_login import UserMixin
from pydantic import BaseModel
from pydantic import Field
from utils import datetime_encoders

from library import login_manager


@login_manager.user_loader
def load_user(user_id: str):

    return User.get(PydanticObjectId(user_id)).run()


class Address(BaseModel):
    street: str
    city: str
    postal_code: str
    country: str

    def __str__(self):
        return f"{self.street}, {self.city}, {self.postal_code}, {self.country}"


class User(UserMixin, Document):
    first_name: str
    last_name: str
    email: Indexed(str)
    phone_number: Indexed(str)
    password: str
    address: Address
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: Optional[datetime.datetime] = None
    is_admin: bool = False

    class Settings:
        bson_encoders = {**datetime_encoders}
