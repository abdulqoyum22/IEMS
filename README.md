# Income and Expenditure Management System (IEMS)

IEMS is an offline desktop financial-recording system for the Computer Engineering Students Association (CESA). It records income and expenditure, produces financial reports, and maintains an audit trail.

## Technology

- Frontend: HTML, CSS, JavaScript
- Backend: Python and Flask
- Desktop wrapper: PyWebView
- Database: SQLite
- Reports: ReportLab (PDF) and OpenPyXL (Excel)

The application is intentionally structured so the frontend remains normal web code while Python handles the financial rules, storage, authentication, and exports.

## Development setup

1. Create and activate a virtual environment: `python3 -m venv .venv` then `source .venv/bin/activate`.
2. Install dependencies: `pip install -r requirements.txt`.
3. Run `python3 run.py --browser` during frontend development.
4. Run `python3 run.py` to launch the local desktop window.

The database and generated reports will be created locally and are not committed to Git.

## Project status

Foundation in progress. The first implementation milestone is the application shell and database schema, followed by authentication and transaction management.

## Documentation

- [Architecture](docs/architecture.md)
- [Frontend handoff](docs/frontend-handoff.md)
