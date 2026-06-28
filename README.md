# Personal Finance & Budget Advisor

A Flask web application for tracking income and expenses, managing budgets
and saving goals, importing bank statements, and getting AI/ML-powered
spending insights.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Flask, SQLAlchemy, Flask-WTF, Flask-Login, Flask-Mail |
| Frontend | Jinja2, Bootstrap 5, Chart.js, vanilla JavaScript |
| Database | MySQL (production), SQLite (development) |
| Data / ML | Pandas, NumPy, Scikit-learn |
| Reports | ReportLab (PDF), OpenPyXL (Excel) |
| Deployment | Gunicorn, Nginx (optional), Docker (optional) |

See `docs/` for the full architecture, database schema, and module
reference produced during planning.

## Project structure

```
app.py            Application factory / entry point
config.py          A single flat Config class with all settings
extensions.py       Flask extension instances (db, login, mail, bcrypt, csrf)
models.py           SQLAlchemy models
forms.py             WTForms form classes
auth/, dashboard/, transactions/, budgets/, goals/, categories/,
reports/, currency/, notifications/, ai/, ml/, api/
                      Flask Blueprints, one package per feature area
services/             Shared business logic
utils/                  Reusable helpers
templates/, static/      Jinja2 templates and CSS/JS/images
tests/                    Pytest test suite
```

## Getting started

### 1. Clone and create a virtual environment

```bash
git clone <your-repo-url>
cd finance-budget-advisor
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure settings (optional)

This project keeps configuration simple — values live directly in
`config.py` instead of a `.env` file. The defaults work out of the box
with no setup: SQLite database, CSRF off, no email credentials needed
yet. If you want to send real emails later (OTP, password reset), open
`config.py` and fill in `MAIL_USERNAME` / `MAIL_PASSWORD` directly in the
`Config` class.

To use MySQL instead of the default SQLite, edit `SQLALCHEMY_DATABASE_URI`
in `config.py`:

```python
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://db_user:db_password@localhost:3306/finance_db"
```

### 4. Run the app

```bash
flask --app app run --debug
```

The app starts at `http://127.0.0.1:5000`.

### 5. Run tests

```bash
pip install pytest
pytest
```

## Configuration reference

All settings below live as plain class attributes in `config.py` —
edit them directly there if you need a different value.

| Setting | Description |
|---|---|
| `SECRET_KEY` | Flask session signing key |
| `SQLALCHEMY_DATABASE_URI` | Database connection string; defaults to local SQLite |
| `MAIL_SERVER` / `MAIL_PORT` / `MAIL_USE_TLS` / `MAIL_USE_SSL` | SMTP connection settings, defaulted for Gmail |
| `MAIL_USERNAME` / `MAIL_PASSWORD` | Placeholder values — replace with real credentials once email features are built |
| `WTF_CSRF_ENABLED` | Currently `False` — see note below |

## Notes on current state

`auth/routes.py` and `dashboard/routes.py` currently contain minimal
placeholder views so the application factory has real blueprints to
register end-to-end. They are replaced incrementally as each module
(see Phase 1–5 in the project structure document) is implemented.

**This project does not use Flask-Bcrypt or CSRF protection.** Password
hashing uses `werkzeug.security.generate_password_hash` /
`check_password_hash` instead (see `models.py`) — no extra dependency,
and still a properly salted hash. CSRF protection is switched off via
`WTF_CSRF_ENABLED = False` in `config.py`, and the `CSRFProtect`
extension itself has been removed from `extensions.py`/`app.py` rather
than just disabled. If this project ever moves beyond a college build —
handling real account data in a real deployment — re-introducing CSRF
protection is worth revisiting, since it's what stops a malicious site
from submitting forged requests (e.g. a fake "delete transaction" form)
using a logged-in user's own session.

