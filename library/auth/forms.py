from flask_wtf import FlaskForm
from wtforms import EmailField
from wtforms import PasswordField
from wtforms import SearchField
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import EqualTo
from wtforms.validators import Length
from wtforms.validators import ValidationError

from library.auth.models import User


class RegisterForm(FlaskForm):
    first_name = StringField(
        "First name",
        validators=[DataRequired(), Length(max=100, message="First name too long")],
    )
    last_name = StringField(
        "Last name", validators=[DataRequired(), Length(max=100, message="Last name too long")]
    )
    email = EmailField("Email", validators=[DataRequired(), Email(message="Invalid email")])
    phone_number = StringField(
        "Phone number",
        validators=[DataRequired(), Length(max=100, message="Phone number too long")],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm password", validators=[DataRequired(), EqualTo("password")]
    )

    street = StringField(
        "Street", validators=[DataRequired(), Length(max=100, message="Street too long")]
    )
    city = StringField(
        "City", validators=[DataRequired(), Length(max=100, message="City too long")]
    )
    postal_code = StringField(
        "Postal code",
        validators=[DataRequired(), Length(max=100, message="Postal code too long")],
    )
    country = StringField(
        "Country", validators=[DataRequired(), Length(max=100, message="Country too long")]
    )
    submit = SubmitField("Sign Up")

    def validate_email(self, email):
        user = User.find_one(User.email == email.data).run()

        if user:
            raise ValidationError("This email is taken.")

    def validate_phone_number(self, phone_number):
        user = User.find_one(User.phone_number == phone_number.data).run()

        if user:
            raise ValidationError("This phone number is taken.")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email(message="Invalid email")])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class SearchUserForm(FlaskForm):
    first_name = SearchField("First name")
    last_name = SearchField("Last name")
    email = SearchField("Email")
    phone_number = SearchField("Phone number")

    submit = SubmitField("Search")
