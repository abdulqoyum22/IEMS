# Deployment Guide

## Railway Deployment Support

This repository has been extended to support Railway deployment while preserving the existing desktop and offline mode.

### Flask application entry point

- Railway entry point: `wsgi.py`
- This file inserts `src` into Python path and then imports `create_app()` from `iems`.
- Production web server object: `application`

### Startup command for Railway

- Railway will start the app with:
  - `gunicorn wsgi:application --bind 0.0.0.0:$PORT`
- This command is defined in `Procfile` and `railway.json`.

### Environment variables

- `IEMS_ENVIRONMENT=production`
  - Enables production configuration.
- `IEMS_SECRET_KEY`
  - Overrides the Flask `SECRET_KEY` in production.
- `DATABASE_URL` (optional)
  - If set, Flask-SQLAlchemy will use this value instead of the default SQLite file.
  - If not set, the app uses SQLite at `data/iems.db`.

### SQLite limitations on Railway

- Railway filesystem is ephemeral.
- SQLite will work, but data is not persisted across container restarts, redeploys, or dyno replacements.
- For persistent storage on Railway, configure a managed database and set `DATABASE_URL`.

### Preserved desktop/offline mode

- Existing desktop entry point remains unchanged: `python run.py`
- Browser mode remains unchanged: `python run.py --browser`
- PyWebView and local SQLite support continue to work.
- Use `requirements-desktop.txt` for local desktop development if you need PyWebView.

### Production vs desktop dependencies

- `requirements.txt` is now the production dependency file for Railway and server deployment.
- `requirements-desktop.txt` includes the desktop-only dependency `pywebview` for local desktop/offline mode.

### Files added or updated

- `requirements.txt`
- `requirements-desktop.txt`
- `Procfile`
- `runtime.txt`
- `railway.json`
- `wsgi.py`
- `src/iems/config.py`
- `src/iems/__init__.py`
- `DEPLOYMENT.md`

### Railway deployment steps

1. Push the repository to a Git remote connected to Railway.
2. In the Railway project, set environment variables:
   - `IEMS_ENVIRONMENT=production`
   - `IEMS_SECRET_KEY=<your-secret>`
   - Optional: `DATABASE_URL=<your-database-url>`
3. Railway should detect Python, install `requirements.txt`, and use `Procfile`.
4. The web service will start with the configured `gunicorn` command.
