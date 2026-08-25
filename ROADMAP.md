# Opson — Stack Assessment & Roadmap

Snapshot taken 2026-05-04, after the GaiaRoots → Opson rebrand and frontend pass.

## Current stack

- Django 5.1, server-rendered templates
- SQLite
- Custom `accounts.User` with role (customer / producer / staff)
- Session-based cart (`cart/cart.py`)
- Vanilla CSS design system (`static/css/opson.css`) — no Tailwind, no build step
- Vanilla JS for toasts, video modal, review form
- Apps: `accounts`, `producers`, `catalog`, `cart`, `orders`

## What's working well

- No build step → fast iteration, easy deploys.
- Django admin gets producer/product/order management for free.
- Server-rendered HTML → great SEO, fast first paint.
- Custom CSS palette is consistent and on-brand; the home, producer detail, and product detail pages all match the `index.html` mockup.
- Multi-vendor `Order` → `SubOrder` fan-out with a per-producer status pipeline is the right modelling for the domain.

## Single biggest leverage point: add HTMX

~14 kB, no build step. Replace the `<form action="...">` + full redirect pattern on cart, status transitions, filters, and review submission with `hx-post` returning partial templates. The toast keeps firing from `messages`. The dashboard can auto-poll active sub-orders.

This closes the gap between "hackathon project" and "feels like a product" without changing the mental model. Estimated cost: one focused day.

Suggested first conversion: `cart_add` returning a small fragment that updates the cart count badge in the header + fires a toast, instead of redirecting.

## Risks if this goes past the demo

| Risk | Why it matters | Fix |
| --- | --- | --- |
| **SQLite under concurrent writes** | Whole-DB write lock — concurrent producer status updates will start 500'ing once there are real users. | Migrate to Postgres before going multi-user. |
| **`image_url` as a plain string** | Real producers can't paste URLs from `loremflickr.com`. | Swap `Product.image_url` / `Producer.cover_url` for `ImageField` + Pillow + `MEDIA_ROOT` (or S3 later). |
| **Cart only in session** | Logged-in customers lose cart on device switch. | Add a `Cart` model for authenticated users; keep session cart for guests; merge on login. |
| **No password reset / email verify / producer onboarding** | Hackathon-only flow. Producers are seeded via admin today. | Wire up `django.contrib.auth` reset views + a producer signup form gated by staff approval. |
| **Empty `tests.py` everywhere** | The order state machine has enough branching that a regression will silently break the demo. | Start with 5–10 tests on `SubOrder.transition_to` (allowed transitions, forbidden transitions, multi-vendor aggregate status). |
| **URL-encoded Greek slugs (`%CE%BC%CF%80...`)** | Ugly in the address bar, hard to share. | Either prefix with the PK (`/producer/12-barbagiannis/`) or transliterate Greek to Latin in `Producer.save()`. |

## What I would NOT do

- Introduce React / Vue / Next. The product is forms and lists. An SPA buys nothing here and costs build complexity, hydration, and a second mental model. HTMX is the right rung on the ladder.
- Tailwind. The current CSS is small enough that purging isn't a problem yet, and the `:root` variables already give you design-token discipline.
- Celery / background workers. Email and order notifications can use Django's built-in mail backend until volume justifies a queue.

## Out of scope (memory: hackathon MVP)

Per project memory, these are deliberately deferred and remain so:

- Stripe Connect / real payments
- Reels videos (kept as static demo content)
- Events (kept as static demo content)
- Reviews (kept as static demo content)
- Producer signup flow (producers seeded, added via admin)

## Suggested order of work post-hackathon

1. **HTMX pass** on cart + producer dashboard transitions (highest perceived-quality lift).
2. **Tests** on the order state machine (cheapest insurance).
3. **Image uploads** so real producers can onboard.
4. **Postgres migration** before opening to real users.
5. **Auth polish**: password reset, producer signup with staff approval.
6. **DB-backed cart** for authenticated users.
