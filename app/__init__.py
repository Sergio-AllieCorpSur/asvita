# app/__init__.py
from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from app.database.db import get_database_url
from app.extensions import db
from app.routes import register_routes
from pathlib import Path
import os

migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # DB / Core
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_url()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config.setdefault("MAX_CONTENT_LENGTH", 32 * 1024 * 1024)

    # Uploads
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    upload_root = os.getenv("UPLOAD_FOLDER") or str(
        Path(app.instance_path) / "uploads")
    app.config["UPLOAD_FOLDER"] = upload_root
    Path(upload_root).mkdir(parents=True, exist_ok=True)

    # Extensiones
    db.init_app(app)
    from app.database.models import dataroom, folder, file, user, membership, audit_log  # noqa
    migrate.init_app(app, db)

    # CORS
    CORS(app, resources={
         r"/api/*": {"origins": ["http://localhost:3000", "*"]}})

    # Rutas / Swagger (RESTX)
    register_routes(app)

    # Errores JSON
    @app.errorhandler(ValueError)
    def handle_value_error(e):
        return jsonify({"error": str(e)}), 400

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"error": "not found"}), 404

    return app
