# Income and Expenditure Management System (IEMS)

## Overview

IEMS is a web-based financial management system for the Computer Engineering Students Association (CESA). It provides a controlled workspace for recording income and expenditure, monitoring balances, producing financial reports, managing user access, and maintaining an audit trail of important activity.

The application supports income tracking, expenditure tracking, dashboard summaries, financial reporting, audit logging, user management, and role-based access control.

## Features

### Authentication & Access Control

- Secure username and password login using Werkzeug password hashing.
- Role-based permissions for administrators and standard users.
- Initial administrator setup and administrator-created user accounts.
- Account-request workflow requiring administrator approval before access is granted.
- Password-reset request workflow handled by an administrator.

### Financial Management

- Create, edit, filter, and soft-delete income and expenditure records.
- Categorise transactions and record dates, descriptions, references, sources, and payees.
- View total income, total expenditure, available balance, monthly activity, and expense allocation on the dashboard.
- Generate date-range financial summaries and analytics.

### User Management

- Create administrator or treasurer accounts.
- Activate or deactivate user accounts.
- Review, approve, or reject account requests.
- Review password-reset requests and set temporary passwords after verification.

### Audit & Accountability

- Logs important actions including login/logout, user administration, access requests, password resets, transaction changes, and report exports.
- Retains audit history for administrator review.

### Reports & Export

- Generate reports for a selected date range.
- Download reports as PDF.
- Export reports as Excel workbooks.

## Technology Stack

| Area | Technology |
| --- | --- |
| Frontend | HTML5, CSS3, JavaScript |
| Backend | Python, Flask |
| Database | SQLite for local development; PostgreSQL through `DATABASE_URL` for production deployment |
| ORM | Flask-SQLAlchemy, SQLAlchemy |
| Authentication security | Werkzeug password hashing, Flask-Login |
| Reporting | ReportLab, OpenPyXL |
| Deployment | Railway, Gunicorn |
| Version control | Git, GitHub |

## Application Architecture

The application follows a simple web architecture:

- **Frontend:** A responsive HTML, CSS, and JavaScript interface presents authentication, dashboard, transaction, reporting, and administration screens.
- **Backend:** Flask routes provide the web page and JSON API endpoints, validate input, enforce permissions, coordinate business rules, and create audit entries.
- **Database:** SQLAlchemy models store users, categories, income, expenditure, signup requests, password-reset requests, and audit logs. Local development defaults to `data/iems.db`.
- **Authentication:** Flask-Login manages authenticated sessions. Passwords are stored as hashes, and administrator-only endpoints use role checks.
- **Reporting:** A report service aggregates transactions for a date range; Flask returns the summary to the UI or creates PDF and Excel downloads.

## Installation & Local Development

### Prerequisites

- Python 3.10 or later

### Setup

1. Clone the repository and enter the project directory.

   ```bash
   git clone <repository-url>
   cd IEMS
   ```

2. Create and activate a virtual environment.

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the web application dependencies.

   ```bash
   pip install -r requirements.txt
   ```

4. Start the local browser-development server.

   ```bash
   python3 run.py --browser
   ```

5. Open `http://127.0.0.1:5000` in a browser. On first use, create the initial administrator account.

The default local SQLite database is created automatically at `data/iems.db` along with the default transaction categories.

### Optional Local Desktop Mode

The project also retains an optional PyWebView desktop launcher. Install the desktop dependency file, then run:

```bash
pip install -r requirements-desktop.txt
python3 run.py
```

## User Roles

### Administrator

Administrators have all standard financial-management permissions and can additionally:

- Create, activate, and deactivate user accounts.
- Review and approve or reject account requests.
- Review password-reset requests and reset user passwords.
- View the audit log.

### Standard User (Treasurer)

Standard users can sign in and use the financial workspace to view the dashboard, manage income and expenditure records, and generate or export reports. They cannot access user management, request administration, or audit logs.

## Access Request Workflow

1. A prospective user submits an account request with their name, username, role request, and password.
2. The request remains pending and is visible to administrators.
3. An administrator reviews the request and approves or rejects it.
4. Approved requests create an active user account; rejected requests do not grant access.

## Password Reset Workflow

1. A user submits a password-reset request using their username.
2. An administrator reviews the pending request and verifies the user's identity.
3. The administrator sets a new temporary password.
4. The administrator shares the temporary credentials with the user through an approved channel.

## Deployment

IEMS is configured for Railway deployment.

- `wsgi.py` exposes the Flask application for production.
- `Procfile` and `railway.json` start Gunicorn with `gunicorn wsgi:application --bind 0.0.0.0:$PORT`.
- Set `IEMS_ENVIRONMENT=production` and a secure `IEMS_SECRET_KEY` in Railway.
- Set `DATABASE_URL` to use a managed PostgreSQL database in production.

`DATABASE_URL` is optional locally: when it is not provided, IEMS uses SQLite at `data/iems.db`. Railway's filesystem is ephemeral, so a managed PostgreSQL database is required for persistent production data.

## Current Status

IEMS is a functional, deployed financial management application. It includes authentication, role-based administration, account-request and password-reset workflows, financial transaction management, reporting and export, audit logging, and Railway deployment support.

## Additional Documentation

- [Deployment guide](DEPLOYMENT.md)
