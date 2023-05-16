from os import environ

from flask import Flask
from flask_pymongo import PyMongo

mongo = PyMongo()


def create_app():
    app = Flask(__name__)
    app.config["MONGO_URI"] = environ.get("MONGO_URI", "mongodb://localhost:27017/library")
    mongo.init_app(app)

    from library.books.routes import books

    app.register_blueprint(books)

    return app
