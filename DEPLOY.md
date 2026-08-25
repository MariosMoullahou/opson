# Deploying the Opson demo to `https://demo.eopson.gr`

This runbook deploys the Opson Django app as a live demo on the existing VPS,
alongside (and without disturbing) the `eopson.gr` landing page.

**Stack:** gunicorn + nginx + Let's Encrypt, SQLite, WhiteNoise for static.
**Coexistence:** this app uses its own systemd service (`opson.service`), its own
gunicorn socket (`/run/opson.sock`), and its own nginx server block. It does not
touch the existing `eopson.gr` site or the other project already running on the box.

---

## Step 0 — Push the repo somewhere the VPS can clone

This project now has its own dedicated git repo. Create a remote (GitHub/GitLab)
and push, so the VPS can clone it:

```bash
# from your local machine, in the project folder:
git remote add origin <your-repo-url>   # e.g. git@github.com:MariosMoullahou/opson.git
git push -u origin main
```

> No GitHub? Alternative: copy the folder to the VPS with
> `rsync -av --exclude venv --exclude .env --exclude db.sqlite3 ./ user@vps:/var/www/opson/`
> and skip the `git clone` in Step 2.

---

## Step 1 — Cloudflare DNS (the `eopson.gr` zone)

1. Cloudflare → select the **eopson.gr** zone → **DNS → Records → Add record**.
2. Set:
   - **Type:** `A`
   - **Name:** `demo`  (Cloudflare expands this to `demo.eopson.gr`)
   - **IPv4 address:** your **VPS public IP**
   - **TTL:** Auto
3. **Proxy status:** set to **DNS only (grey cloud)** before running certbot, so
   Let's Encrypt's HTTP-01 challenge reaches the server directly.
   - Simplest for a demo: **leave it grey-cloud**. HTTPS still works via the
     Let's Encrypt cert issued in Step 7.
   - If you later want Cloudflare's proxy/CDN (orange cloud), turn it on **after**
     the cert is issued, and set Cloudflare **SSL/TLS mode = "Full (strict)"**.
     (Do **not** use "Flexible" — combined with this app's SSL-redirect it causes
     a redirect loop.)

Confirm DNS resolves before continuing: `dig +short demo.eopson.gr` → your VPS IP.

---

## Step 2 — Clone + virtualenv (on the VPS)

```bash
sudo mkdir -p /var/www/opson && sudo chown $USER:$USER /var/www/opson
git clone <your-repo-url> /var/www/opson
cd /var/www/opson
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

---

## Step 3 — Environment file

```bash
cp .env.example .env

# generate a fresh secret key:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# edit .env: paste the key as SECRET_KEY, keep:
#   DEBUG=False
#   ALLOWED_HOSTS=demo.eopson.gr
#   CSRF_TRUSTED_ORIGINS=https://demo.eopson.gr
#
# Media: leave AWS_STORAGE_BUCKET_NAME blank to keep uploads on local disk,
# or fill the bucket, region, CloudFront domain and AWS credentials to use S3.
nano .env
```

> **SECRET_KEY is now mandatory.** There is no fallback key any more: with `.env` missing or
> `SECRET_KEY` unset the app raises `KeyError` on startup rather than silently booting in debug
> mode with `ALLOWED_HOSTS=['*']`. If gunicorn will not start, check this first.

---

## Step 4 — Django setup

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py catalog_load_data     # load demo data (idempotent, safe to re-run)
python manage.py createsuperuser
```

`catalog_load_data` upserts on natural keys and never deletes, so it is safe to run again on a
live demo, orders and all. Pass `--dry-run` to see what it would change first.

To wipe the demo catalog instead, use `catalog_reset_demo` — the only command in the project that
deletes anything. It refuses to run while any `Order` exists unless given `--force`.

### Running the demo without S3

Leave `AWS_STORAGE_BUCKET_NAME` blank in `.env` and Django writes uploads to `media/` on
disk instead of S3 — no code change and no extra dependency. The nginx block in
`deploy/nginx-demo.eopson.gr.conf` serves that directory at `/media/`, which is required
because WhiteNoise does not serve user media and Django refuses to with `DEBUG=False`.

Make sure the directory exists and gunicorn's user can write to it:

```bash
mkdir -p /var/www/opson/media && chown $USER:www-data /var/www/opson/media
```

Uploads on local disk are **not** backed up by anything. Fine for a demo; move to S3 before
any real producer relies on it.

### Verify the media pipeline by hand

Seed data leaves every image field blank, so nothing on deploy exercises uploads. Check it once,
manually:

1. Sign in as a producer and open **Dashboard → Επεξεργασία** on any product.
2. Upload a JPEG or PNG and save.
3. Confirm two `.webp` objects appear under `products/` in the bucket (or in `media/products/`
   when running on local disk).
4. Confirm the card and detail images render on the storefront through CloudFront.

If the upload fails with `AccessControlListNotSupported`, the bucket has ACLs disabled and
`default_acl` is not `None` — see the S3 section of the design spec.

---

## Step 5 — gunicorn via systemd

```bash
sudo cp deploy/opson.service /etc/systemd/system/opson.service
# If your clone path or service user differ, edit WorkingDirectory / PATH / User
# in /etc/systemd/system/opson.service before continuing.

# gunicorn (running as www-data) must be able to read AND write db.sqlite3
# and read the project files:
sudo chown -R www-data:www-data /var/www/opson

sudo systemctl daemon-reload
sudo systemctl enable --now opson
sudo systemctl status opson    # expect: active (running)
```

If it fails, check logs: `sudo journalctl -u opson -e`.

---

## Step 6 — nginx site

```bash
sudo cp deploy/nginx-demo.eopson.gr.conf /etc/nginx/sites-available/demo.eopson.gr
sudo ln -s /etc/nginx/sites-available/demo.eopson.gr /etc/nginx/sites-enabled/
sudo nginx -t                  # must pass and must NOT affect the eopson.gr site
sudo systemctl reload nginx
```

---

## Step 7 — HTTPS via certbot

certbot is already present (the other project uses HTTPS). If not:
`sudo apt install certbot python3-certbot-nginx`

```bash
sudo certbot --nginx -d demo.eopson.gr
```

certbot edits the nginx site to add the `listen 443` TLS block and a HTTP→HTTPS
redirect, then reloads nginx.

---

## Step 8 — Verify

- `https://demo.eopson.gr` → Opson app loads, styled (CSS/JS via WhiteNoise),
  valid padlock, demo data present.
- `https://demo.eopson.gr/admin/` → reachable, log in with the superuser.
- `https://eopson.gr` → landing page unchanged.

---

## Redeploying after future changes

```bash
cd /var/www/opson
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart opson
```
