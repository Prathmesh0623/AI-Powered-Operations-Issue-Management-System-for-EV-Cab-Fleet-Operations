# Deployment Guide

## Production Configuration

`config/config.py` defines three configs, selected via the `FLASK_ENV`
environment variable:

- `development` (default) — debug on, SQLite allowed, dev secrets allowed
- `production` — debug off; **fails fast at startup** if `SECRET_KEY` /
  `JWT_SECRET_KEY` are still the insecure defaults, or if `DATABASE_URL` is
  still pointing at SQLite. This is deliberate: a misconfigured production
  deploy should crash immediately with a clear error, not silently run
  insecurely.
- `testing` — in-memory SQLite, used by the Pytest suite

## Required Environment Variables (Production)

```
FLASK_ENV=production
SECRET_KEY=<a long random value>
JWT_SECRET_KEY=<a different long random value>
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<dbname>
```

Generate strong secrets, e.g.:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Database Migrations

This prototype currently provisions its schema via `db.create_all()` in
`database/seed_data.py`, which is fine for a demo/prototype but not for an
evolving production schema. Flask-Migrate is already a dependency
(`requirements.txt`) and wired into `app.py` (`Migrate(app, db)`); to start
using proper migrations instead:

```bash
flask db init
flask db migrate -m "initial schema"
flask db upgrade
```

From that point on, schema changes go through `flask db migrate` +
`flask db upgrade` rather than `create_all()`.

## Static Files

In production, Flask itself should not serve static files directly at
scale — front them with a reverse proxy (Nginx) or a CDN, pointing at the
`static/` directory. `static/` contains no build step (no bundler) — it's
plain CSS/JS served as-is.

## Running with Gunicorn

```bash
pip install -r requirements.txt   # includes gunicorn
gunicorn wsgi:app --workers 4 --bind 0.0.0.0:8000 --timeout 120
```

`wsgi.py` exposes the Flask app instance as `app` via the same
`create_app()` factory used everywhere else, so dev and prod always
construct the app identically.

A `Procfile` is included for platforms that use one (Heroku-style):
```
web: gunicorn wsgi:app --workers 4 --bind 0.0.0.0:$PORT --timeout 120
```

## Reverse Proxy (Nginx example)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/ai-operations-management/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## ML Models in Production

Trained `.pkl` files under `ml/models/` and `ml/vectorizers/` need to exist
on the deployed instance — either committed (as this prototype does, for a
"just works" demo) or built as a release-time step (`python
ml/training/train_category.py && python ml/training/train_priority.py`)
before the app starts. They are loaded once per process at import time, so
a model update requires a process restart to take effect — there is no
hot-reload.

## Pre-Deployment Checklist

- [ ] `FLASK_ENV=production` set, with real `SECRET_KEY`/`JWT_SECRET_KEY`
- [ ] `DATABASE_URL` points at a real PostgreSQL instance, not SQLite
- [ ] Database migrated (or `seed_data.py` run once for initial baseline data)
- [ ] `ml/models/*.pkl` and `ml/vectorizers/*.pkl` present on the deployed instance
- [ ] Static files served via reverse proxy/CDN, not Flask's dev server
- [ ] Gunicorn (or equivalent WSGI server) — never Flask's built-in dev server — fronts the app
- [ ] HTTPS terminated at the reverse proxy/load balancer
- [ ] `.env` is not committed to version control (already covered by `.gitignore`)

## What This Project Does NOT Yet Include

Being transparent about scope: there is no CI/CD pipeline, no containerization
(Dockerfile), no monitoring/alerting integration, and no automated backup
strategy configured in this repository. These are reasonable next steps for
a real deployment but are outside this prototype's current scope (see
"Future Enhancements" in the README).
