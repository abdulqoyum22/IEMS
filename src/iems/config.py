"""Application configuration values."""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class DevelopmentConfig:
    """Safe defaults for local development."""

    SECRET_KEY = os.environ.get("IEMS_SECRET_KEY", "iems-development-key-change-before-release")
    DATABASE_DIRECTORY = PROJECT_ROOT / "data"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_DIRECTORY / 'iems.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
