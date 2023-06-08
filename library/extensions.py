from os import environ

from pymongo import MongoClient

mongo_client = MongoClient(environ.get("MONGO_URI", "mongodb://localhost:27017/"))
