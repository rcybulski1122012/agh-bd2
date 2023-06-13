import datetime
import math
import random
from decimal import Decimal

from bunnet import PydanticObjectId
from faker import Faker
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
from library.auth.decorators import admin_role_required
from library.auth.models import User
from library.books.forms import AddBookForm
from library.books.forms import ModifyBookForm
from library.books.forms import AddReviewForm
from library.books.forms import FilterBooksForm
from library.books.forms import RentBookForm
from library.books.models import Book
from library.books.models import Rent
from library.books.models import Review

books = Blueprint("books", __name__)

faker = Faker()

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
        "isbn": request.args.get("isbn", None),
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
    reviews = Review.find(Review.book_id == PydanticObjectId(book_id), fetch_links=True).run()

    already_rented = bool(
        Rent.find_one(
            Rent.book.id == PydanticObjectId(book_id),
            Rent.user.id == PydanticObjectId(current_user.id),
        ).run()
    )

    review_added = bool(
        Review.find_one(
            Review.book_id == PydanticObjectId(book_id),
            Review.user.id == PydanticObjectId(current_user.id),
        ).run()
    )

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

    return render_template(
        "books/book_detail.html",
        book=book,
        form=form,
        reviews=reviews,
        already_rented=already_rented,
        review_added=review_added,
    )


@books.route("/books/<book_id>/rent/<user_id>", methods=["GET"])
@login_required
@admin_role_required
def rent_book(book_id, user_id):
    user = User.get(user_id).run()
    book = Book.get(book_id).run()
    rent = Rent.find_one(
        Rent.book.id == PydanticObjectId(book_id),
        Rent.user.id == PydanticObjectId(user_id),
        Rent.return_date == None,  # noqa
    ).run()

    if not book or not user:
        raise abort(404)

    if rent:
        flash("Book already rented", "danger")
        return redirect(book.detail_url)

    if not book.is_available:
        raise abort(403)

    with mongo_client.start_session() as session, session.start_transaction():
        book.stock -= 1
        book.save(session=session)
        rent = Rent(book=book, user=user)
        rent.save(session=session)

    flash("Book rented successfully", "success")
    return redirect(url_for("auth.user_details", user_id=user_id))


@books.route("/books/<book_id>/return/<user_id>", methods=["GET"])
@login_required
@admin_role_required
def return_book(book_id, user_id):
    rent = Rent.find_one(
        Rent.book.id == PydanticObjectId(book_id),
        Rent.user.id == PydanticObjectId(user_id),
        Rent.return_date == None,  # noqa
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
        book = Book.get(book_id).run()
        book.delete()
        flash("Book has been removed", "success")
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


@books.route("/returns/overdue", methods=["GET"])
def overdue_returns():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 24, type=int)

    query = Rent.get_overdue().find(fetch_links=True).sort(Rent.due_date)
    rents = query.skip((page - 1) * page_size).limit(page_size).run()
    total = query.count()

    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": math.ceil(total / page_size),
    }

    return render_template("books/overdue_returns.html", rents=rents, pagination=pagination)


@books.route("/books/<book_id>/add_review", methods=["GET", "POST"])
def add_review(book_id):
    book = Book.get(book_id).run()

    review = Review.find_one(
        Review.book_id == PydanticObjectId(book_id),
        Review.user.id == PydanticObjectId(current_user.id),
    ).run()

    rent = Rent.find_one(
        Review.book_id == PydanticObjectId(book_id),
        Review.user.id == PydanticObjectId(current_user.id),
    )

    if not book:
        abort(404)

    if review:
        abort(403)

    if not rent:
        abort(403)

    form = AddReviewForm()
    if request.method == "POST" and form.validate_on_submit():
        rating = Decimal(form.rating.data)
        with mongo_client.start_session() as session, session.start_transaction():
            review = Review(
                book_id=book_id,
                user=current_user,
                rating=rating,
                comment=form.comment.data,
            )
            book.add_review(rating)
            book.save(session=session)
            review.save(session=session)

        flash("New review has been added", "success")
        return redirect(url_for("books.book_detail", book_id=book_id))

    return render_template("books/add_review.html", form=form, book=book)

@books.route("/books/modify/<book_id>", methods=["GET", "POST"])
@login_required
@admin_role_required
def modify_book(book_id):
    form = ModifyBookForm(book_id)
    if request.method == "POST" and form.validate_on_submit():
        book = Book.get(book_id).run()
        book.title = form.title.data
        book.authors=form.authors.data.split(",")
        book.topic=form.topic.data
        book.genre=form.genre.data
        book.publication_date=form.publication_date.data
        book.publisher=form.publisher.data
        book.description=form.description.data
        book.isbn=form.isbn.data
        book.pages=form.pages.data
        book.stock=form.stock.data
        book.initial_stock=form.stock.data
        book.images_urls=[faker.image_url() for _ in range(random.randint(1, 3))]

        book.authors = book.authors[0].split(",")
        book.save()
        flash("Book has been modified", "success")
        return redirect(url_for("books.list_books"))
    
    return render_template("books/add_book.html", form=form)

    
