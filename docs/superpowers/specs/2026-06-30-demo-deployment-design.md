# Opson Demo Deployment Design

**Date:** 2026-06-30
**Goal:** Make the Opson Django project ready to host a live demo at `https://demo.eopson.gr` on an existing VPS, without disturbing the existing `eopson.gr` landing page.

## Context

- Django 5.1.4 marketplace MVP. Apps: accounts, producers, catalog, cart, orders.
- Current `settings.py` is dev-only: `DEBUG=True`, hardcoded insecure `SECRET_KEY`, `ALLOWED_HOSTS=["*"]`, no `STATIC_ROOT`, no production security.
- Database: **SQLite** (kept for the demo — single server, light traffic).
- No media uploads: models use URL fields (e.g. `cover_url`), not `ImageField`/`FileField`. No `MEDIA_ROOT` needed.
- A `seed` management command exists (`catalog/management/commands/seed.py`) for demo data.
- VPS already provisioned, SSH access ready. Existing landing page served at `eopson.gr` (the `landing/` dir is a separate git repo, gitignored).

## Decisions

| Decision | Choice |
|---|---|
| Host | Existing VPS (Ubuntu assumed), gunicorn + nginx |
| Domain | `demo.eopson.gr` (subdomain; `eopson.gr` untouched) |
| Database | SQLite (kept) |
| HTTPS | Yes — Let's Encrypt cert for `demo.eopson.gr` only |
| Static files | WhiteNoise (gunicorn serves static; nginx just proxies) |
| Out of scope (YAGNI) | Postgres, media handling, Docker, CI/CD |

## Changes

### 1. `opson/settings.py` — environment-driven

Read from environment with safe dev defaults (local dev keeps working unchanged):

- `SECRET_KEY` — from env; dev fallback to current insecure key.
- `DEBUG` — from env (`"False"` in prod); defaults `True` for local.
- `ALLOWED_HOSTS` — from env, comma-separated; dev default `["*"]`. Prod: `demo.eopson.gr`.
- `CSRF_TRUSTED_ORIGINS` — from env; prod: `https://demo.eopson.gr`.
- `STATIC_ROOT = BASE_DIR / "staticfiles"` and WhiteNoise storage backend.
- Add WhiteNoise middleware directly after `SecurityMiddleware`.
- Production-only block (when `DEBUG=False`):
  - `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` (behind nginx)
  - `SECURE_SSL_REDIRECT = True`
  - `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`
  - HSTS (`SECURE_HSTS_SECONDS`, include subdomains, preload)
- Load `.env` via `python-dotenv` if present.

### 2. Repo config files

- **`requirements.txt`** (new): `Django==5.1.4`, `djangorestframework==3.16.1`, `gunicorn`, `whitenoise`, `python-dotenv`.
- **`.env.example`** (new): documents `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`.
- **`.gitignore`** (update): add `.env`, `db.sqlite3`, `staticfiles/`, `__pycache__/`, `*.pyc`, `venv/`.

### 3. Server artifacts + guide

- **`deploy/opson.service`** — gunicorn systemd unit.
- **`deploy/nginx-demo.eopson.gr.conf`** — nginx server block for `demo.eopson.gr` (proxy to gunicorn). Separate file; does not touch existing `eopson.gr` config.
- **`DEPLOY.md`** — step-by-step:
  1. DNS: add A record `demo.eopson.gr` → VPS IP.
  2. Clone repo, create venv, `pip install -r requirements.txt`.
  3. Create `.env` with prod values (generate fresh `SECRET_KEY`).
  4. `migrate`, `collectstatic`, `seed`, `createsuperuser`.
  5. Install systemd service, start gunicorn (bind to unix socket or 127.0.0.1:8000).
  6. Install nginx site, enable, reload.
  7. `certbot --nginx -d demo.eopson.gr` for SSL.

## Success criteria

- `https://demo.eopson.gr` serves the Opson app with valid SSL, styled (static files load), demo data seeded, admin reachable.
- `eopson.gr` landing page continues to work unchanged.
- Local development still runs with `python manage.py runserver` and no `.env`.
