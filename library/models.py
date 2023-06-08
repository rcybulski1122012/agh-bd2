from dataclasses import dataclass
from datetime import date
from datetime import datetime
from typing import Optional


@dataclass
class Book:
    _id: str
    name: str
    author: str
    quantity: int
    no_available: int
    no_pages: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Borrowing:
    _id: str
    book_id: str
    user_id: str
    is_returned: bool
    borrowed_at: datetime
    return_date: Optional[date]


@dataclass
class Address:
    country: str
    city: str
    street: str
    building_number: str
    flat_number: Optional[str] = None


@dataclass
class User:
    _id: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    password: str
    address: Address
    created_at: str
    updated_at: str
