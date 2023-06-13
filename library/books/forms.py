from datetime import datetime

from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DateField
from wtforms import IntegerField
from wtforms import DateField
from wtforms import IntegerField
from wtforms import SearchField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import StringField
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms.validators import Length

from library.books.models import BookGenre
from library.books.models import BookOrders

ORDER_CHOICES = [(x.value, x.value) for x in BookOrders]  # type: ignore
GENRE_CHOICES = [("", "Select a genre")] + [(x.value, x.value) for x in BookGenre]  # type: ignore


class FilterBooksForm(FlaskForm):
    title = SearchField("Title")
    genre = SelectField("Genre", choices=GENRE_CHOICES, default="")  # type: ignore
    author = SearchField("Author")
    isbn = SearchField("ISBN")
    available = BooleanField("Only available", default=False)
    order_by = SelectField("Order by", choices=ORDER_CHOICES, default="none")

    submit = SubmitField("Filter")


class RentBookForm(FlaskForm):
    email_or_phone_number = SearchField("Email or phone number", validators=[DataRequired()])
    submit = SubmitField("Rent")


class AddBookForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[DataRequired(), Length(max=100, message="Title too long")],
        default="Witcher",
    )
    authors = StringField(
        "Authors",
        validators=[DataRequired(), Length(max=100, message="Authors too long")],
        default="Steve Smith",
    )
    topic = StringField(
        "Topic",
        validators=[DataRequired(), Length(max=100, message="Topic too long")],
        default="Fighting",
    )
    genre = SelectField("Genre", choices=GENRE_CHOICES, default="Fantasy")  # type: ignore

    publication_date = DateField(
        "Publication date (YYYY-MM-DD)", validators=[DataRequired()], default=datetime.now()
    )
    publisher = StringField(
        "Publisher",
        validators=[DataRequired(), Length(max=100, message="Publisher too long")],
        default="Book publisher",
    )
    description = StringField(
        "Description",
        validators=[DataRequired(), Length(max=100, message="Description too long")],
        default="Nice book",
    )
    isbn = StringField(
        "ISBN",
        validators=[DataRequired(), Length(max=100, message="ISBN not valid")],
        default="1234567890",
    )
    pages = IntegerField("Pages", validators=[DataRequired()], default=345)
    stock = IntegerField("Stock", validators=[DataRequired()], default=5)
    submit = SubmitField("Add")


class AddReviewForm(FlaskForm):
    rating = SelectField(
        "Rating", validators=[DataRequired()], choices=[(x, x) for x in range(1, 6)]
    )
    comment = StringField("Comment", validators=[DataRequired()])
    submit = SubmitField("Add")
