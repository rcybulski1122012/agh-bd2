from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import SearchField
from wtforms import SelectField
from wtforms import SubmitField
from wtforms import StringField
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms.validators import ValidationError
from datetime import datetime

from library.books.models import BookGenre
from library.books.models import BookOrders

ORDER_CHOICES = [(x.value, x.value) for x in BookOrders]  # type: ignore
GENRE_CHOICES = [("", "Select a genre")] + [(x.value, x.value) for x in BookGenre]  # type: ignore


class FilterBooksForm(FlaskForm):
    title = SearchField("Title")
    genre = SelectField("Genre", choices=GENRE_CHOICES, default="")  # type: ignore
    author = SearchField("Author")
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
        default='Witcher'
    )
    authors = StringField(
        "Authors", validators=[DataRequired(), Length(max=100, message="Authors too long")],
        default='Steve Smith'
    )
    topic = StringField(
        "Topic",
        validators=[DataRequired(), Length(max=100, message="Topic too long")],
        default='Fighting'
    )
    genre = SelectField("Genre", choices=GENRE_CHOICES, default='Fantasy')  # type: ignore

    publication_date = StringField(
        "Publication date (YYYY-MM-DD)", validators=[DataRequired(), Length(max=100, message="Publication date too long")],
        default='2010-12-13'
    )
    publisher = StringField(
        "Publisher",
        validators=[DataRequired(), Length(max=100, message="Publisher too long")],
        default='Book publisher'
    )
    description = StringField(
        "Description", validators=[DataRequired(), Length(max=100, message="Description too long")],
        default='Nice book'
    )
    pages = StringField(
        "Pages", validators=[DataRequired(), Length(max=100, message="Pages too long")],
        default='345'
    )
    stock = StringField(
        "Stock", validators=[DataRequired(), Length(max=100, message="Stock too long")],
        default='5'
    )
    submit = SubmitField("Add")

    def validate_pages(self, field):
        try:
            int(field.data)
        except ValueError:
            raise ValidationError("Pages must be a valid number.")
        
    def validate_stock(self, field):
        try:
            int(field.data)
        except ValueError:
            raise ValidationError("Stock must be a valid number.")
        
    def validate_publication_date(self, field):
        try:
            datetime.strptime(field.data, '%Y-%m-%d')
        except ValueError:
            raise ValidationError("Publication date must be in the format YYYY-MM-DD.")
        
    def validate_genre(self, field):
        if not field.data:
            raise ValidationError("Genre must not be empty.")
