"""IEMS application package."""

import os

from flask import Flask

from iems.config import DevelopmentConfig, ProductionConfig
from iems.extensions import db, login_manager
from iems.models import seed_default_categories
from iems.routes.main import main_blueprint


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    environment = os.environ.get("IEMS_ENVIRONMENT", "development").lower()
    if environment == "production":
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    app.config["DATABASE_DIRECTORY"].mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.home"
    app.register_blueprint(main_blueprint)

    with app.app_context():
        db.create_all()
        seed_default_categories()

    return app
