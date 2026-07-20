"""Development and desktop launch entry point for IEMS."""

from __future__ import annotations

import argparse
import threading
import sys
from pathlib import Path

from werkzeug.serving import make_server

# Makes the source package runnable without an installation step during development.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from iems import create_app


def run_in_browser(app) -> None:
    """Run the local Flask server for HTML/CSS/JavaScript development."""
    app.run(host="127.0.0.1", port=5000, debug=True)


def run_as_desktop_app(app) -> None:
    """Serve Flask locally inside a native PyWebView window."""
    import webview

    server = make_server("127.0.0.1", 5000, app)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    webview.create_window("IEMS | CESA", "http://127.0.0.1:5000", min_size=(1024, 700))
    webview.start()
    server.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch IEMS.")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Open as a local development server rather than a desktop window.",
    )
    arguments = parser.parse_args()
    application = create_app()

    if arguments.browser:
        run_in_browser(application)
    else:
        run_as_desktop_app(application)
