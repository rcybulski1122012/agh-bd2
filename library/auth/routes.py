from auth.forms import LoginForm
from auth.forms import RegisterForm
from auth.models import Address
from auth.models import User
from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_user
from flask_login import logout_user

from library import bcrypt

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        user = User.find_one(User.email == form.email.data).run()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get("next")
            flash("You have been logged in!", "success")
            return redirect(next_page) if next_page else redirect(url_for("main.home"))
        else:
            flash("Login Unsuccessful. Please check email and password", "danger")
    return render_template("auth/login.html", form=form)


@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.home"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = RegisterForm()
    if request.method == "POST" and form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            password=hashed_password,
            address=Address(
                street=form.street.data,
                city=form.city.data,
                postal_code=form.postal_code.data,
                country=form.country.data,
            ),
        )
        user.insert()
        flash("Your account has been created! You are now able to log in", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)
