import datetime

from flask import Blueprint
from flask import render_template
from models import Address
from models import Book
from models import Rent
from models import User

books = Blueprint("books", __name__)


@books.route("/", methods=["GET", "POST"])
def create_book():

    book = Book(
        title="Test",
        authors=["Test"],
        topic="Test",
        publication_date=datetime.date.today(),
        publisher="Test",
        isbn="Test",
        pages=1,
        stock=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )

    book.insert()

    user = User(
        first_name="Test",
        last_name="Test",
        email="test@test.pl",
        phone_number="123456789",
        address=Address(street="Test", city="Test", postal_code="Test", country="Test"),
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )

    user.insert()

    rent = Rent(
        book_id=book.id,
        user_id=user.id,
        rent_date=datetime.date.today(),
        due_date=datetime.date.today(),
        return_date=datetime.date.today(),
    )

    rent.insert()

    return render_template("books/create_book.html")
