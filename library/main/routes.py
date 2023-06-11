from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import url_for
from flask_login import current_user

main = Blueprint("main", __name__)


@main.route("/")
@main.route("/home")
def home():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))

    return render_template("home.html")
