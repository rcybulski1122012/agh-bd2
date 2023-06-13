from os import environ

from bunnet import init_bunnet
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from pymongo import MongoClient


mongo_client = MongoClient(environ.get("MONGO_URI", "mongodb://localhost:27017/"))
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app():
    app = Flask(__name__)
    app.config["DEBUG"] = True
    app.config["SECRET_KEY"] = "!9)m$3d@gnm5hwhy16r(je*l1y1ry)xs!58c77se0_3p9596^4"

    login_manager.init_app(app)
    bcrypt.init_app(app)

    from library.books.models import Book
    from library.auth.models import User
    from library.books.models import Rent
    from library.books.models import Review

    init_bunnet(database=mongo_client["library"], document_models=[Book, User, Rent, Review])

    from library.books.routes import books
    from library.main.routes import main
    from library.auth.routes import auth

    app.register_blueprint(books)
    app.register_blueprint(main)
    app.register_blueprint(auth)

    return app
