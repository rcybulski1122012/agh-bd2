import math

from flask import Blueprint
from flask import render_template
from flask import request

from library.books.forms import FilterBooksForm
from library.books.models import Book

books = Blueprint("books", __name__)


@books.route("/books", methods=["GET"])
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

    print(filters)
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

    print(pagination)

    return render_template(
        "books/list_books.html",
        form=form,
        books=books_,
        pagination=pagination,
        filters_query_string=filters_query_string,
    )
