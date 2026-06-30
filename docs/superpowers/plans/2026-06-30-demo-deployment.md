# Opson Demo Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Opson Django project deployable as a live demo at `https://demo.eopson.gr` on the existing VPS (gunicorn + nginx + Cloudflare DNS + Let's Encrypt), without disturbing the existing `eopson.gr` landing page.

**Architecture:** `settings.py` becomes environment-driven (12-factor) with safe dev defaults so local `runserver` still works. WhiteNoise serves static via gunicorn. A dedicated systemd unit (`opson.service`) runs gunicorn on its own unix socket (`/run/opson.sock`); a dedicated nginx server block proxies `demo.eopson.gr` to that socket. Cloudflare holds the DNS A record; certbot issues the cert.

**Tech Stack:** Django 5.1.4, djangorestframework 3.16.1, gunicorn, whitenoise, python-dotenv, SQLite, nginx, systemd, certbot, Cloudflare DNS.

## Global Constraints

- Python 3.12, Django 5.1.4 (do not upgrade).
- SQLite stays the database — no Postgres.
- Local dev MUST keep working with `python manage.py runserver` and **no** `.env` file present.
- Do NOT modify or reference the existing `eopson.gr` nginx config or the `landing/` directory (separate git repo, gitignored).
- New server resources use the name `opson` to avoid collisions with the user's other gunicorn/nginx project: service `opson.service`, socket `/run/opson.sock`, nginx site `demo.eopson.gr`.
- No media handling (models use URL fields, not ImageField/FileField).
- Production domain: `demo.eopson.gr`. CSRF origin: `https://demo.eopson.gr`.

---

### Task 1: Make settings.py environment-driven

**Files:**
- Modify: `opson/settings.py`
- Create: `.env.example`

**Interfaces:**
- Produces: env vars consumed at deploy time — `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` (comma-separated), `CSRF_TRUSTED_ORIGINS` (comma-separated). Produces `STATIC_ROOT = BASE_DIR / "staticfiles"`.

- [ ] **Step 1: Add dotenv loading + env helpers at top of settings.py**

After the `BASE_DIR` line in `opson/settings.py`, add:

```python
import os

# Load .env if present (no-op in local dev when the file is absent).
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


def env_bool(name, default):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


def env_list(name, default):
    raw = os.environ.get(name)
    return [item.strip() for item in raw.split(",") if item.strip()] if raw else default
```

- [ ] **Step 2: Replace SECRET_KEY, DEBUG, ALLOWED_HOSTS**

Replace the existing `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` lines with:

```python
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-xfv9q0w6m#4^4s1x-=g)2h)@g*t*l16_1omnv779m8&ti#-zxz",
)

DEBUG = env_bool("DEBUG", True)

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", ["*"])

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", [])
```

- [ ] **Step 3: Add STATIC_ROOT + WhiteNoise storage**

Replace the static files block near the bottom with:

```python
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

- [ ] **Step 4: Add WhiteNoise middleware**

In `MIDDLEWARE`, insert `'whitenoise.middleware.WhiteNoiseMiddleware',` immediately after `'django.middleware.security.SecurityMiddleware',`.

- [ ] **Step 5: Add production security block at end of settings.py**

```python
# Production hardening — active only when DEBUG is off.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 2592000  # 30 days
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
```

- [ ] **Step 6: Create .env.example**

```
# Copy to .env on the server and fill in real values. Do NOT commit .env.
SECRET_KEY=replace-with-a-fresh-50-char-random-string
DEBUG=False
ALLOWED_HOSTS=demo.eopson.gr
CSRF_TRUSTED_ORIGINS=https://demo.eopson.gr
```

- [ ] **Step 7: Verify local dev still works (no .env)**

Run: `python manage.py check`
Expected: `System check identified no issues`.

Run: `python manage.py runserver` (then Ctrl-C) — confirm it boots with `DEBUG=True` defaults.

- [ ] **Step 8: Verify production mode parses**

Run: `DEBUG=False ALLOWED_HOSTS=demo.eopson.gr CSRF_TRUSTED_ORIGINS=https://demo.eopson.gr SECRET_KEY=test python manage.py check --deploy`
Expected: runs without configuration errors (deploy warnings about HSTS/SSL are expected and fine).

- [ ] **Step 9: Commit**

```bash
git add opson/settings.py .env.example
git commit -m "Make settings environment-driven for production"
```

---

### Task 2: Add requirements.txt and update .gitignore

**Files:**
- Create: `requirements.txt`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: nothing.
- Produces: `requirements.txt` installable with `pip install -r requirements.txt`.

- [ ] **Step 1: Create requirements.txt**

```
Django==5.1.4
djangorestframework==3.16.1
gunicorn==23.0.0
whitenoise==6.8.2
python-dotenv==1.0.1
```

- [ ] **Step 2: Append to .gitignore**

Add these lines (keep the existing `landing/` line):

```
# Python / Django
__pycache__/
*.pyc
venv/
.venv/

# Local secrets and data
.env
db.sqlite3

# Collected static
staticfiles/
```

- [ ] **Step 3: Verify install resolves**

Run: `pip install -r requirements.txt`
Expected: all packages install (whitenoise, gunicorn, python-dotenv newly added). gunicorn is Linux-targeted; on the Windows dev box it may warn but installs — it is only used on the server.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt .gitignore
git commit -m "Add requirements.txt and harden .gitignore"
```

---

### Task 3: Add server artifacts (systemd + nginx)

**Files:**
- Create: `deploy/opson.service`
- Create: `deploy/nginx-demo.eopson.gr.conf`

**Interfaces:**
- Consumes: gunicorn from requirements, the unix socket `/run/opson.sock`.
- Produces: deployable systemd + nginx config templates referenced by DEPLOY.md.

- [ ] **Step 1: Create deploy/opson.service**

Template (paths edited on the server to match the clone location and user):

```ini
[Unit]
Description=Opson demo (gunicorn)
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/opson
Environment="PATH=/var/www/opson/venv/bin"
ExecStart=/var/www/opson/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/opson.sock \
    opson.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 2: Create deploy/nginx-demo.eopson.gr.conf**

```nginx
server {
    listen 80;
    server_name demo.eopson.gr;

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/opson.sock;
    }
}
```

Note: WhiteNoise serves `/static/` through gunicorn, so no nginx `static` location is needed. certbot rewrites this file to add the TLS `listen 443` block.

- [ ] **Step 3: Commit**

```bash
git add deploy/opson.service deploy/nginx-demo.eopson.gr.conf
git commit -m "Add systemd and nginx deploy templates for demo.eopson.gr"
```

---

### Task 4: Write DEPLOY.md (including Cloudflare steps)

**Files:**
- Create: `DEPLOY.md`

**Interfaces:**
- Consumes: all prior artifacts (settings env vars, requirements, deploy templates).
- Produces: the human runbook. No code.

- [ ] **Step 1: Write DEPLOY.md with the full runbook**

Content covers, in order:

1. **Cloudflare DNS**
   - Log in to Cloudflare → select the `eopson.gr` zone → **DNS → Records → Add record**.
   - Type `A`, Name `demo`, IPv4 = the VPS public IP, TTL Auto.
   - **Proxy status:** set to **DNS only (grey cloud)** for the initial certbot run, so Let's Encrypt's HTTP-01 challenge reaches the server directly. After the cert is issued you may switch it back to **Proxied (orange cloud)**; if you do, set Cloudflare **SSL/TLS mode to "Full (strict)"** so it trusts the Let's Encrypt cert. Leaving it grey-cloud is simplest for a demo.

2. **Server: clone + venv**
   ```bash
   sudo mkdir -p /var/www/opson && sudo chown $USER:$USER /var/www/opson
   git clone <repo-url> /var/www/opson
   cd /var/www/opson
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Environment file**
   ```bash
   cp .env.example .env
   # generate a fresh secret key:
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   # paste it into .env as SECRET_KEY, keep DEBUG=False, ALLOWED_HOSTS=demo.eopson.gr,
   # CSRF_TRUSTED_ORIGINS=https://demo.eopson.gr
   nano .env
   ```

4. **Django setup**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py seed          # load demo data
   python manage.py createsuperuser
   ```

5. **gunicorn via systemd**
   ```bash
   sudo cp deploy/opson.service /etc/systemd/system/opson.service
   # edit WorkingDirectory/PATH/User in the unit if your paths differ
   sudo chown -R www-data:www-data /var/www/opson   # so gunicorn can read db.sqlite3 + write it
   sudo systemctl daemon-reload
   sudo systemctl enable --now opson
   sudo systemctl status opson    # confirm active (running)
   ```

6. **nginx site**
   ```bash
   sudo cp deploy/nginx-demo.eopson.gr.conf /etc/nginx/sites-available/demo.eopson.gr
   sudo ln -s /etc/nginx/sites-available/demo.eopson.gr /etc/nginx/sites-enabled/
   sudo nginx -t                  # must pass without touching existing eopson.gr site
   sudo systemctl reload nginx
   ```

7. **HTTPS via certbot**
   ```bash
   sudo certbot --nginx -d demo.eopson.gr
   ```
   (certbot is already installed since the other project uses HTTPS; if not: `sudo apt install certbot python3-certbot-nginx`.)

8. **Verify**
   - Visit `https://demo.eopson.gr` — app loads, styled, padlock valid.
   - Visit `https://eopson.gr` — landing page unchanged.
   - `/admin/` reachable with the superuser.

9. **Redeploy (after future git pushes)**
   ```bash
   cd /var/www/opson && git pull
   source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate && python manage.py collectstatic --noinput
   sudo systemctl restart opson
   ```

- [ ] **Step 2: Commit**

```bash
git add DEPLOY.md
git commit -m "Add deployment runbook for demo.eopson.gr"
```

---

## Self-Review

**Spec coverage:**
- Env-driven settings (SECRET_KEY/DEBUG/ALLOWED_HOSTS/CSRF/STATIC_ROOT/WhiteNoise/security) → Task 1 ✓
- requirements.txt + .env.example + .gitignore → Tasks 1 & 2 ✓
- systemd + nginx artifacts → Task 3 ✓
- DEPLOY.md runbook (DNS, clone, env, migrate/collectstatic/seed/superuser, gunicorn, nginx, certbot) → Task 4 ✓
- Cloudflare (added per user request) → Task 4 Step 1 ✓
- Coexistence with existing project (unique names, don't touch eopson.gr) → Global Constraints + Task 3/4 ✓
- Local dev still works → Task 1 Steps 7–8 ✓

**Placeholder scan:** `<repo-url>` in DEPLOY.md is an intentional user-supplied value, documented in context. No other placeholders.

**Type consistency:** `env_bool` / `env_list` defined in Task 1 Step 1 and used in Step 2 — consistent. Socket `/run/opson.sock` and service `opson.service` consistent across Tasks 3 & 4.
