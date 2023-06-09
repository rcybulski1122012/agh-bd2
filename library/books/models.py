import datetime
from typing import Optional

from bunnet import Document
from bunnet import Indexed
from bunnet import PydanticObjectId
from pydantic import Field

from library.utils import datetime_encoders
from library.utils import next_month_factory


class Book(Document):
    title: Indexed(str)
    authors: list[str]
    topic: str
    publication_date: datetime.date
    publisher: Indexed(str)
    isbn: Indexed(str)
    pages: int
    stock: int
    images_urls: list[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Settings:
        bson_encoders = {**datetime_encoders}


class Rent(Document):
    book_id: Indexed(PydanticObjectId)
    user_id: Indexed(PydanticObjectId)
    rent_date: datetime.date = Field(default_factory=datetime.date.today)
    due_date: datetime.date = Field(default_factory=next_month_factory)
    return_date: Optional[datetime.date] = None

    class Settings:
        bson_encoders = {**datetime_encoders}
