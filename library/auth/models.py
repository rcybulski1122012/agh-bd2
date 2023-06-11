import datetime
from typing import Optional

from bunnet import Document
from bunnet import Indexed
from bunnet import PydanticObjectId
from bunnet.odm.operators.find.evaluation import RegEx
from flask import url_for
from flask_login import UserMixin
from pydantic import BaseModel
from pydantic import Field

from library import login_manager
from library.utils import datetime_encoders


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
    first_name: Indexed(str)
    last_name: Indexed(str)
    email: Indexed(str, unique=True)
    phone_number: Indexed(str, unique=True)
    password: str
    address: Address
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: Optional[datetime.datetime] = None
    is_admin: bool = False

    class Settings:
        bson_encoders = {**datetime_encoders}

    @classmethod
    def filter(
        cls,
        first_name: str = None,
        last_name: str = None,
        email: str = None,
        phone_number: str = None,
    ):
        query = cls.find()

        if first_name:
            query = query.find(
                RegEx(cls.first_name, f".*{first_name}.*", "i"),
            )

        if last_name:
            query = query.find(
                RegEx(cls.last_name, f".*{last_name}.*", "i"),
            )

        if email:
            query = query.find(
                RegEx(cls.email, f".*{email}.*", "i"),
            )

        if phone_number:
            query = query.find(
                RegEx(cls.phone_number, f".*{phone_number}.*", "i"),
            )

        return query

    @property
    def details_url(self):
        return url_for("auth.user_details", user_id=self.id)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
