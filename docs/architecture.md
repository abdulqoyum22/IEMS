# IEMS architecture

IEMS is an offline-first desktop application for CESA. It runs a Flask server only on the user's computer and displays it in a PyWebView desktop window. SQLite stores data in a local database file.

```text
HTML / CSS / JavaScript interface
              |
          Flask routes
              |
     Service / business rules
              |
 Repository / SQLAlchemy models
              |
          SQLite database
```

The frontend must never access the SQLite database directly. Flask routes receive browser requests; services validate permissions and financial rules; repositories/models persist data. This separation lets the same frontend be deployed as a web version later without redesigning it.

## Planned modules

| Area | Responsibility |
| --- | --- |
| `routes` | Pages and JSON endpoints |
| `services` | Authentication, finance, reports, audit rules |
| `models` | Database entities |
| `repositories` | Reusable data retrieval and storage operations |
| `templates` | HTML screens built by the frontend owner |
| `static` | CSS, JavaScript, images, and icons |

## Delivery path

1. Develop locally with `python run.py --browser`.
2. Launch the offline desktop app with `python run.py`.
3. Later package it with PyInstaller and publish installers via GitHub Releases.
4. If an online version is desired, deploy Flask to a Python host and migrate SQLite to PostgreSQL; the frontend can remain largely unchanged.
