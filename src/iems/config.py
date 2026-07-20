"""Application configuration values."""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class BaseConfig:
    """Common configuration for all environments."""

    SECRET_KEY = os.environ.get("IEMS_SECRET_KEY", "iems-development-key-change-before-release")
    DATABASE_DIRECTORY = PROJECT_ROOT / "data"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{DATABASE_DIRECTORY / 'iems.db'}",
    )


class DevelopmentConfig(BaseConfig):
    """Safe defaults for local development and desktop mode."""


class ProductionConfig(BaseConfig):
    """Production-ready defaults for web deployment."""

    SECRET_KEY = os.environ.get("IEMS_SECRET_KEY", "change-this-secret-for-production")
