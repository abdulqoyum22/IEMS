"""WSGI entry point for Railway and other web deployments."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from iems import create_app

application = create_app()
