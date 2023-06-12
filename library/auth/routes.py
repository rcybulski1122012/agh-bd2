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
from flask_login import login_user
from flask_login import logout_user

from library import bcrypt
from library.auth.decorators import admin_role_required
from library.auth.forms import LoginForm
from library.auth.forms import RegisterForm
from library.auth.forms import SearchUserForm
from library.auth.models import Address
from library.auth.models import User
from library.books.models import Rent

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


@auth.route("/members", methods=["GET"])
@login_required
@admin_role_required
def member_list():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 24, type=int)

    filters = {
        "first_name": request.args.get("first_name", None),
        "last_name": request.args.get("last_name", None),
        "email": request.args.get("email", None),
        "phone_number": request.args.get("phone_number", None),
    }

    form = SearchUserForm(**filters)
    filters_query_string = "&".join([f"{k}={v}" for k, v in filters.items() if v])

    query = User.filter(**filters)
    users = query.skip((page - 1) * page_size).limit(page_size).run()
    total = query.count()

    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": math.ceil(total / page_size),
    }

    return render_template(
        "auth/member_list.html",
        form=form,
        users=users,
        pagination=pagination,
        filters_query_string=filters_query_string,
    )


@auth.route("/members/<user_id>", methods=["GET"])
@login_required
def user_details(user_id):
    user = User.get(user_id).run()

    if not current_user.is_admin and current_user.id != user.id:
        abort(403)

    if not user:
        abort(404)

    rents = (
        Rent.find(Rent.user_id == PydanticObjectId(user_id), fetch_links=True)
        .sort(-Rent.rent_date)
        .run()
    )
    already_returned = [rent for rent in rents if rent.return_date]
    not_returned = [rent for rent in rents if not rent.return_date]

    return render_template(
        "auth/user_details.html",
        user=user,
        already_returned=already_returned,
        not_returned=not_returned,
    )
