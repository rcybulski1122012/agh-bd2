from flask import Blueprint
from flask import render_template

books = Blueprint("books", __name__)


@books.route("/book", methods=["GET", "POST"])
def create_book():
    return render_template("books/create_book.html")
