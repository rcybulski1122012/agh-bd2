import datetime

from bunnet import Document
from bunnet import Indexed
from bunnet import init_bunnet
from bunnet import PydanticObjectId
from extensions import mongo_client
from pydantic import BaseModel

datetime_encoders = {
    datetime.date: lambda x: x.isoformat(),
    datetime.datetime: lambda x: x.isoformat(),
}


class Book(Document):
    title: Indexed(str)
    authors: list[str]
    topic: str
    publication_date: datetime.date
    publisher: Indexed(str)
    isbn: Indexed(str)
    pages: int
    stock: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Settings:
        bson_encoders = {**datetime_encoders}


class Address(BaseModel):
    street: str
    city: str
    postal_code: str
    country: str

    def __str__(self):
        return f"{self.street}, {self.city}, {self.postal_code}, {self.country}"


class User(Document):
    first_name: str
    last_name: str
    email: Indexed(str)
    phone_number: Indexed(str)
    address: Address
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Settings:
        bson_encoders = {**datetime_encoders}


class Rent(Document):
    book_id: Indexed(PydanticObjectId)
    user_id: Indexed(PydanticObjectId)
    rent_date: datetime.date
    due_date: datetime.date
    return_date: datetime.date

    class Settings:
        bson_encoders = {**datetime_encoders}


init_bunnet(database=mongo_client["library"], document_models=[Book, User, Rent])
