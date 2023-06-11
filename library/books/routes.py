import datetime
import math

from bunnet import PydanticObjectId
from flask import abort
from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_required

from library import mongo_client
from library.books.forms import FilterBooksForm
from library.books.models import Book
from library.books.models import Rent

books = Blueprint("books", __name__)


@books.route("/books", methods=["GET"])
@login_required
def list_books():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 24, type=int)

    filters = {
        "title": request.args.get("title", None),
        "genre": request.args.get("genre", None),
        "author": request.args.get("author", None),
        "available": request.args.get("available", None, type=bool),
        "order_by": request.args.get("order_by", None),
    }
    form = FilterBooksForm(**filters)
    filters_query_string = "&".join([f"{k}={v}" for k, v in filters.items() if v])

    query = Book.filter(**filters)
    books_ = query.skip((page - 1) * page_size).limit(page_size).run()
    total = query.count()

    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": math.ceil(total / page_size),
    }

    return render_template(
        "books/list_books.html",
        form=form,
        books=books_,
        pagination=pagination,
        filters_query_string=filters_query_string,
    )


@books.route("/books/<book_id>", methods=["GET"])
@login_required
def book_detail(book_id):
    book = Book.get(book_id).run()

    return render_template("books/book_detail.html", book=book)


@books.route("/books/<book_id>/rent/<user_id>", methods=["GET", "POST"])
@login_required
def rent_book(book_id, user_id):
    book = Book.get(book_id).run()
    rent = Rent.find_one({"book_id": book_id, "user_id": user_id}).run()

    if not book or (rent and not rent.return_date):
        raise abort(404)

    if not book.is_available:
        raise abort(403)

    with mongo_client.start_session() as session, session.start_transaction():
        book.stock -= 1
        book.save(session=session)
        rent = Rent(
            book_id=book.id,
            user_id=current_user.id,
        )
        rent.save(session=session)

    flash("Book rented successfully", "success")
    return redirect(url_for("auth.user_detail", user_id=user_id))


@books.route("/books/<book_id>/return/<user_id>", methods=["GET", "POST"])
@login_required
def return_book(book_id, user_id):
    rent = Rent.find_one(
        {
            "book_id": PydanticObjectId(book_id),
            "user_id": PydanticObjectId(user_id),
            "return_date": None,
        }
    ).run()

    print(rent)

    if not rent:
        raise abort(404)

    with mongo_client.start_session() as session, session.start_transaction():
        book = Book.get(book_id).run()
        book.stock += 1
        book.save(session=session)
        rent.return_date = datetime.date.today().isoformat()
        rent.save(session=session)

    flash("Book returned successfully", "success")
    return redirect(url_for("auth.user_details", user_id=user_id))
