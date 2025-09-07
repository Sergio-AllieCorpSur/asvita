
from flask import Flask
from flask_migrate import Migrate
from app.database.db import get_database_url
from app.extensions import db

migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_url()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)

    # models import
    from app.database.models import dataroom, folder, file, user, membership, audit_log, mixins

    return app
