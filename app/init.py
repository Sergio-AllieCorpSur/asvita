# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.database.db import get_database_url

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_url()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app
