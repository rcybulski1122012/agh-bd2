import datetime
import math
import random

from bunnet import PydanticObjectId
from faker import Faker
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
from library.auth.decorators import admin_role_required
from library.auth.models import User
from library.books.forms import AddBookForm
from library.books.forms import FilterBooksForm
from library.books.forms import RentBookForm
from library.books.models import Book
from library.books.models import Rent

books = Blueprint("books", __name__)

faker = Faker()

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


@books.route("/books/<book_id>", methods=["GET", "POST"])
@login_required
def book_detail(book_id):
    book = Book.get(book_id).run()

    form = RentBookForm()
    if request.method == "POST":
        if not current_user.is_admin:
            abort(403)

        user = (
            User.find_one({"email": form.email_or_phone_number.data}).run()
            or User.find_one({"email": form.email_or_phone_number.data}).run()
        )

        if not user:
            flash("User not found", "danger")
            return redirect(url_for("books.book_detail", book_id=book_id))

        return redirect(url_for("books.rent_book", book_id=book_id, user_id=str(user.id)))

    return render_template("books/book_detail.html", book=book, form=form)


@books.route("/books/<book_id>/rent/<user_id>", methods=["GET"])
@login_required
@admin_role_required
def rent_book(book_id, user_id):
    book = Book.get(book_id).run()
    rent = Rent.find_one(
        {
            "book_id": PydanticObjectId(book_id),
            "user_id": PydanticObjectId(user_id),
            "return_date": None,
        }
    ).run()

    if not book:
        raise abort(404)

    if rent:
        flash("Book already rented", "danger")
        return redirect(book.detail_url)

    if not book.is_available:
        raise abort(403)

    with mongo_client.start_session() as session, session.start_transaction():
        book.stock -= 1
        book.save(session=session)
        rent = Rent(
            book_id=book.id,
            book=book,
            user_id=user_id,
        )
        rent.save(session=session)

    flash("Book rented successfully", "success")
    return redirect(url_for("auth.user_details", user_id=user_id))


@books.route("/books/<book_id>/return/<user_id>", methods=["GET"])
@login_required
@admin_role_required
def return_book(book_id, user_id):
    rent = Rent.find_one(
        {
            "book_id": PydanticObjectId(book_id),
            "user_id": PydanticObjectId(user_id),
            "return_date": None,
        }
    ).run()

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


@books.route("/books/remove/<book_id>", methods=["GET"])
@login_required
@admin_role_required
def remove_book(book_id):
    try:
        result = Book.delete_one({"_id": PydanticObjectId(book_id)})
        if result.deleted_count == 1:
            flash("Book has been removed", "success")
        else:
            flash("Book not found", "error")
    except Exception:
        flash("Removing error", "error")

    return redirect(url_for("books.list_books"))


@books.route("/books/add_book", methods=["GET", "POST"])
@login_required
@admin_role_required
def add_book():
    form = AddBookForm()
    if request.method == "POST" and form.validate_on_submit():
        book = Book(
            title=form.title.data,
            authors=form.authors.data.split(","),
            topic=form.topic.data,
            genre=form.genre.data,
            publication_date=form.publication_date.data,
            publisher=form.publisher.data,
            description=form.description.data,
            isbn=form.isbn.data,
            pages=form.pages.data,
            stock=form.stock.data,
            initial_stock=form.stock.data,
            images_urls=[faker.image_url() for _ in range(random.randint(1, 3))],
        )
        book.authors = book.authors[0].split(",")
        book.save()
        flash("New book has been added", "success")
        return redirect(url_for("books.list_books"))

    return render_template("books/add_book.html", form=form)
