import datetime
from enum import Enum
from typing import Optional

from bunnet import Document
from bunnet import Indexed
from bunnet import Link
from bunnet.odm.operators.find.array import ElemMatch
from bunnet.odm.operators.find.evaluation import RegEx
from flask import url_for
from pydantic import Field

from library.auth.models import User
from library.utils import datetime_encoders
from library.utils import next_month_factory


class BookOrders(str, Enum):
    NONE = "None"
    TITLE_ASC = "Title Ascending"
    TITLE_DSC = "Title Descending"
    PAGES_ASC = "Pages Ascending"
    PAGES_DSC = "Pages Descending"
    PUB_DATE_ASC = "Publication Date Ascending"
    PUB_DATE_DSC = "Publication Date Descending"


class BookGenre(str, Enum):
    FANTASY = "Fantasy"
    SCIENCE_FICTION = "Science Fiction"
    HORROR = "Horror"
    THRILLER = "Thriller"
    ROMANCE = "Romance"
    MYSTERY = "Mystery"
    DETECTIVE = "Detective"
    DYSTOPIAN = "Dystopian"
    HISTORICAL_FICTION = "Historical Fiction"
    MEMOIR = "Memoir"
    COOKBOOK = "Cookbook"
    BIOGRAPHY = "Biography"
    ART_ARCHITECTURE = "Art & Architecture"
    SELF_HELP = "Self Help"
    HEALTH_FITNESS = "Health & Fitness"
    HISTORY = "History"
    TRAVEL = "Travel"
    GUIDE_HOW_TO = "Guide & How To"
    CHILDREN = "Children"
    COMIC_GRAPHIC_NOVEL = "Comic & Graphic Novel"
    ART = "Art"
    PHOTOGRAPHY = "Photography"
    POETRY = "Poetry"
    HUMOR = "Humor"
    ESSAY = "Essay"
    JOURNAL = "Journal"
    RELIGIOUS = "Religious"
    SPIRITUALITY = "Spirituality"
    ACADEMIC = "Academic"
    TEXTBOOK = "Textbook"
    SCIENCE = "Science"
    MATH = "Math"
    ANTHOLOGY = "Anthology"
    DRAMA = "Drama"
    SHORT_STORY = "Short Story"
    YOUNG_ADULT = "Young Adult"
    OTHER = "Other"


class Book(Document):
    title: Indexed(str)
    authors: list[str]
    topic: str
    genre: BookGenre
    publication_date: datetime.date
    description: str
    publisher: Indexed(str)
    isbn: Indexed(str)
    pages: int
    stock: int
    initial_stock: int
    images_urls: list[str]
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    class Settings:
        bson_encoders = {**datetime_encoders}

    @property
    def detail_url(self):
        return url_for("books.book_detail", book_id=self.id)

    def rent_url(self, user_id: str):
        return url_for("books.rent_book", book_id=self.id, user_id=user_id)

    def return_url(self, user_id: str):
        return url_for("books.return_book", book_id=self.id, user_id=user_id)

    @property
    def is_available(self):
        return self.stock > 0

    @classmethod
    def filter(
        cls,
        title: str = None,
        genre: BookGenre = None,
        author: str = None,
        available: bool = None,
        isbn: str = None,
        order_by: str = None,
    ):
        query = cls.find()

        if title:
            query = query.find(
                RegEx(cls.title, f".*{title}.*", "i"),
            )

        if genre:
            query.find(
                cls.genre == genre,
            )

        if author:
            query.find(
                ElemMatch(cls.authors, {"$regex": author, "$options": "i"}),
            )

        if available:
            query.find(
                cls.stock > 0,
            )

        if isbn:
            query.find(
                RegEx(cls.title, f".*{title}.*", "i"),
            )

        if order_by and order_by != BookOrders.NONE:
            if order_by == BookOrders.TITLE_ASC:
                query = query.sort(cls.title)
            elif order_by == BookOrders.TITLE_DSC:
                query = query.sort(-cls.title)
            elif order_by == BookOrders.PAGES_ASC:
                query = query.sort(cls.pages)
            elif order_by == BookOrders.PAGES_DSC:
                query = query.sort(-cls.pages)
            elif order_by == BookOrders.PUB_DATE_ASC:
                query = query.sort(cls.publication_date)
            elif order_by == BookOrders.PUB_DATE_DSC:
                query = query.sort(-cls.publication_date)

        return query


class Rent(Document):
    book: Link[Book]
    user: Link[User]
    rent_date: datetime.date = Field(default_factory=datetime.date.today)
    due_date: datetime.date = Field(default_factory=next_month_factory)
    return_date: Optional[datetime.date] = None

    class Settings:
        bson_encoders = {**datetime_encoders}

    @property
    def is_overdue(self):
        return not self.return_date and self.due_date < datetime.date.today()

    @classmethod
    def get_overdue(cls):
        return cls.find(
            cls.return_date == None,  # noqa
            cls.due_date < datetime.date.today(),
        )
