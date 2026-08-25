# Opson — Model Redesign + S3 Media + Forms

**Date:** 2026-08-24
**Repo:** https://github.com/MariosMoullahou/opson (public, `main`, 2 commits)
**Status:** Approved design, ready for implementation planning
**In-repo home:** copy this to `docs/superpowers/specs/2026-08-24-model-redesign-s3-design.md`

---

## 0. Context for the implementer

Opson is a Greek multi-vendor local-food marketplace: Django 5.1, server-rendered templates,
SQLite, vanilla CSS, no build step. Apps: `accounts`, `producers`, `catalog`, `cart`, `orders`.

Three facts that shape everything below:

1. **Nothing is in production.** `demo.eopson.gr` serves seeded demo data only. Schema may be
   broken freely; no backfills, no multi-step column renames.
2. **The project follows the terraweb2 ruleset** at `~/Documents/Iqsoft/terraweb2/docs/rules/`
   (14 files). Rules are cited inline below as `rule NN`. Where a rule is DRF-specific it does
   not transfer — opson has no API — but the layering and validation intent does.
3. **This pass is deliberately partial.** It covers models, media and forms. It does NOT build
   the `services/` or `managers/` layers. See §9 for what is knowingly left undone.

### Decisions already made (do not relitigate)

| Decision | Choice |
|---|---|
| Scope | Models + media + forms. No `services/`, no `managers/` |
| Migrations | Clean slate — delete existing files, regenerate `0001_initial` per app |
| S3 delivery | Private bucket + CloudFront OAC; `default_acl = None` |
| Image sizing | Pillow, synchronous on upload, 2 renditions per image |
| AWS | Greenfield — full setup documented in §5 |
| Edit views | Add `product_update` + `profile_update` (none exist today) |
| Demo images | Left blank; existing emoji fallback carries the UI |
| Orphaned files | `django-cleanup` now; reconcile command noted for later |
| Producer URLs | PK-prefixed Greek slug, lookup by pk |
| Seed | Split: `catalog_load_data` (idempotent) + `catalog_reset_demo` (destructive) |
| Stock | Decrement now via conditional UPDATE |
| Settings | `SECRET_KEY`/`DEBUG` hardening included |

---

## 1. New `core/` app

Required by rule 01 (timestamps come from an abstract base in `core`) and rule 00 (`core/` holds
shared infrastructure only — never domain models).

```
core/
    __init__.py
    apps.py
    models.py      CreateUpdateDateModel
    images.py      render_variants(), validate_upload()
    text.py        greek_slug()
```

```python
class CreateUpdateDateModel(Model):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

Add `'core'` to `INSTALLED_APPS`. `core/` gets no migrations for the abstract base.

---

## 2. Schema

### 2.1 `accounts` — delete `User.role`

`role` is a second source of truth that already diverges from reality: `SignupForm` never sets
it, so every signup is `customer` regardless of whether a `Producer` profile exists. Templates
gate on `user.is_producer` (reads `role`) while views gate on `producer_profile` (the relation).
A producer seeded via admin therefore gets a working dashboard with no nav link to it.

Delete the field and the `Role` enum. Derive the property from the relation:

```python
class User(AbstractUser):
    phone = CharField(max_length=32, blank=True)

    @property
    def is_producer(self) -> bool:
        return hasattr(self, 'producer_profile')
```

The three roles remain expressible: staff is Django's `is_staff`, producer is "has a
`producer_profile`", customer is "does not".

**Consequences to handle:**
- `accounts/admin.py` — remove `role` from `list_display`, `list_filter`, and the `Opson` fieldset
- `catalog/management/commands/seed.py` — see §6
- `templates/base.html:25` and `:119` keep working unchanged (`user.is_producer` still resolves)

### 2.2 `enums.py` per app

Rule 08: `TextChoices` live in `<app>/enums.py`, **always**. Never nested in a model class.

| New file | Contents |
|---|---|
| `orders/enums.py` | `OrderStatus`, and `SUBORDER_TRANSITIONS` beside it |
| `producers/enums.py` | `ProducerBadge` (was `Producer.Badge`) |
| `catalog/enums.py` | `ProductUnit` (was `Product.Unit`) |

`accounts/enums.py` is not created — `Role` is being deleted.

Keep comparing against enum members, never string literals — the existing code already does this
correctly and it should stay that way.

### 2.3 Constraints — make the bugs unrepresentable

This is the main prize of a free schema. `CheckConstraint` works on SQLite in Django 5.1, so
these hold even before the Postgres migration.

```python
# orders/models.py
class OrderItem(CreateUpdateDateModel):
    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        constraints = [
            CheckConstraint(condition=Q(quantity__gt=0), name='orderitem_quantity_positive'),
            CheckConstraint(condition=Q(unit_price__gte=0), name='orderitem_unit_price_non_negative'),
        ]

class SubOrder(CreateUpdateDateModel):
    class Meta:
        verbose_name = 'Sub Order'
        verbose_name_plural = 'Sub Orders'
        constraints = [
            UniqueConstraint(fields=['order', 'producer'], name='unique_suborder_per_producer'),
        ]
        indexes = [Index(fields=['status']), Index(fields=['producer', 'status'])]

class Order(CreateUpdateDateModel):
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [Index(fields=['customer', 'created_at'])]
```

```python
# catalog/models.py
class Product(CreateUpdateDateModel):
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        constraints = [
            CheckConstraint(condition=Q(price__gt=0), name='product_price_positive'),
            UniqueConstraint(fields=['producer', 'name'], name='unique_product_name_per_producer'),
        ]
        indexes = [Index(fields=['is_active']), Index(fields=['producer', 'is_active'])]
```

```python
# producers/models.py
class Producer(CreateUpdateDateModel):
    class Meta:
        verbose_name = 'Producer'
        verbose_name_plural = 'Producers'
        constraints = [
            CheckConstraint(condition=Q(rating__gte=0) & Q(rating__lte=5), name='producer_rating_range'),
        ]
```

> **Note on `CheckConstraint`:** the kwarg is `condition=` in Django 5.1+ (`check=` is deprecated).

The `unique_product_name_per_producer` constraint is not cosmetic — §6's idempotent loader
upserts on `(producer, name)` and needs it.

### 2.4 Field changes

| Model | Change | Why |
|---|---|---|
| `Product.slug` | **Delete** | Generated on every save, read by nothing; routes use `pk` |
| `Producer.photo_url` | **Delete** | Not referenced by any template. YAGNI — one migration to add back |
| `Product.image_url` | → `image_card`, `image_detail` | §4 |
| `Producer.cover_url` | → `cover_card`, `cover_detail` | §4 |
| `OrderItem.product` | add `related_name='order_items'` | Rule 01: `related_name` on **every** relation |
| all models | inherit `CreateUpdateDateModel` | `Category` and `OrderItem` currently have no timestamps |
| all models | add `verbose_name` + `verbose_name_plural` | Rule 01; only `Category` has one today |

Keep `Product.emoji` — it is the fallback when no image is uploaded, and §6 relies on it.

Keep `Producer.rating` / `rating_count` as admin-set values. Reviews remain static demo data in
this pass, so there is nothing to compute them from.

### 2.5 Producer slug and URLs

`slugify(farm_name, allow_unicode=False)` returns an **empty string** for every Greek farm name —
Greek has no ASCII decomposition, so NFKD + `encode('ascii', 'ignore')` erases it. Verified
against the real seed data. Latin transliteration would need a GPL-licensed dependency and
handles Greek poorly (μπ → b or mp, ντ → d or nt, γγ → ng, all context-dependent).

**Decision: keep Greek slugs, look up by pk, treat the slug as decorative.**

```python
# core/text.py
def greek_slug(value: str) -> str:
    """Slugify preserving Greek characters. Never returns empty for Greek input."""
    return slugify(value, allow_unicode=True)
```

`Producer.slug` loses `unique=True` — it is no longer an identifier. Keep the `save()` override
that populates it, drop the uniqueness loop.

URL shape:

```python
# catalog/urls.py
path('producer/<int:pk>-<str:slug>/', views.producer_detail, name='producer-detail'),
```

`producer_detail` fetches by `pk`, and if `slug != producer.slug` issues a 301 to the canonical
URL. Renaming a farm then never 404s.

**Move the producer management URLs off the `producer/` prefix.** Today `producers.urls` is
mounted at `producer/` while `catalog.urls` also serves `producer/<slug>/` — two apps sharing one
prefix, against rule 05. Mount `producers.urls` at `dashboard/` instead:

```python
# opson/urls.py
path('dashboard/', include('producers.urls')),

# producers/urls.py
urlpatterns = [
    path('', views.dashboard, name='producer-dashboard'),
    path('profile/', views.profile_update, name='producer-profile'),
    path('products/new/', views.product_create, name='producer-product-create'),
    path('products/<int:pk>/edit/', views.product_update, name='producer-product-edit'),
    path('suborders/<int:pk>/transition/', views.transition_suborder, name='producer-suborder-transition'),
]
```

Route names move to kebab-case throughout (rule 05). Every `{% url %}` tag in `templates/` must
be updated — see §7.

---

## 3. Forms — the missing validation layer

There is currently **no `Form`, `ModelForm`, or serializer anywhere**. Every view reads
`request.POST` raw. That single omission is the root of the review's critical findings.

Rule 04 governs the equivalent DRF layer; its intent maps directly onto Django forms:
validate input, shape output, hold no business logic.

### 3.1 `cart/forms.py`

```python
class CartAddForm(Form):
    """Quantity to add, bounded by what the product actually has."""

    quantity = IntegerField(min_value=1, max_value=99)

    def __init__(self, *args, product: Product, **kwargs):
        self.product = product
        super().__init__(*args, **kwargs)

    def clean_quantity(self) -> int:
        quantity = self.cleaned_data['quantity']
        if quantity > self.product.stock:
            raise ValidationError('Δεν υπάρχει αρκετό απόθεμα.')
        return quantity
```

`CartUpdateForm` is the same with `min_value=0` (0 means remove).

**This kills:** the `quantity=-100` → **−887.50 order total** bug (verified by running the
extracted arithmetic), and the `int('abc')` → HTTP 500 at `cart/views.py:27` and `:38`.

### 3.2 `orders/forms.py`

```python
class CheckoutForm(ModelForm):
    """Delivery details for an order."""

    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'address', 'notes']
```

`full_name`, `phone`, `address` are non-blank model fields, so `ModelForm` requires them
automatically. Today `Order.objects.create()` bypasses validators entirely and defaults them to
`''`, producing orders with no delivery address.

### 3.3 `producers/forms.py`

```python
class ProductForm(ModelForm):
    """Create or edit one of the signed-in producer's products."""

    image = ImageField(required=False, help_text='JPEG, PNG ή WebP. Έως 8MB.')

    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'unit', 'unit_label',
                  'price', 'stock', 'emoji', 'is_active']

    def clean_image(self):
        return validate_upload(self.cleaned_data.get('image'))

    def save(self, commit=True):
        product = super().save(commit=False)
        upload = self.cleaned_data.get('image')
        if upload:
            variants = render_variants(upload, sizes={'card': 400, 'detail': 1000})
            product.image_card = variants['card']
            product.image_detail = variants['detail']
        if commit:
            product.save()
        return product
```

`ProducerProfileForm` is the same shape over `Producer` with
`fields = ['farm_name', 'village', 'region', 'bio', 'badge']` and a `cover` upload rendering
`{'card': 600, 'detail': 1600}`.

> The `producer` FK is **not** a form field. It is set from `request.user.producer_profile` in
> the view. A form field would let a producer post another producer's id.

### 3.4 `accounts/forms.py`

Move `SignupForm` out of `accounts/views.py` (rule 00 — views hold HTTP, nothing else).

---

## 4. Media pipeline

### 4.1 Fields

Four `ImageField`s, two per source upload. One upload produces two renditions.

```python
# catalog/models.py
image_card   = ImageField(upload_to=product_image_path, blank=True)   #  400px
image_detail = ImageField(upload_to=product_image_path, blank=True)   # 1000px

# producers/models.py
cover_card   = ImageField(upload_to=producer_cover_path, blank=True)  #  600px
cover_detail = ImageField(upload_to=producer_cover_path, blank=True)  # 1600px
```

`upload_to` callables produce `products/<uuid4>.webp` / `producers/<uuid4>.webp`. UUID names mean
no collisions, no Greek filenames in S3 keys, and no information leak from the original filename.

### 4.2 `core/images.py`

```python
ALLOWED_FORMATS = frozenset({'JPEG', 'PNG', 'WEBP'})
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_DIMENSION = 6000


def validate_upload(upload):
    """Reject anything that is not a reasonable photo, with a message a producer can act on."""
    if upload is None:
        return None
    if upload.size > MAX_UPLOAD_BYTES:
        raise ValidationError('Η εικόνα είναι πολύ μεγάλη (μέγιστο 8MB).')
    image = Image.open(upload)
    image.verify()                      # verify() consumes the file object
    upload.seek(0)
    image = Image.open(upload)
    if image.format not in ALLOWED_FORMATS:
        raise ValidationError('Δεκτές μορφές: JPEG, PNG, WebP.')
    if max(image.size) > MAX_DIMENSION:
        raise ValidationError('Η εικόνα έχει πολύ μεγάλες διαστάσεις.')
    upload.seek(0)
    return upload


def render_variants(upload, sizes: dict[str, int]) -> dict[str, ContentFile]:
    """Resize one upload into named renditions, stripping EXIF."""
    upload.seek(0)
    source = Image.open(upload)
    source = ImageOps.exif_transpose(source)     # phone photos are rotated via EXIF
    if source.mode != 'RGB':
        source = source.convert('RGB')

    variants = {}
    for name, width in sizes.items():
        variant = source.copy()
        variant.thumbnail((width, width * 4), Image.LANCZOS)   # width-bound, aspect preserved
        buffer = BytesIO()
        variant.save(buffer, format='WEBP', quality=82, method=6)
        variants[name] = ContentFile(buffer.getvalue())
    return variants
```

Two things this must do, both easy to omit:

- **`ImageOps.exif_transpose()` before resizing.** Phone photos carry an EXIF orientation flag.
  Without this, farm photos render sideways.
- **Re-encode without EXIF.** Saving to a fresh buffer drops the metadata, which also strips
  **GPS coordinates**. A producer's home location should not ship with their honey photo.

**HEIC:** iPhones shoot HEIC and Pillow cannot open it unopposed. iOS Safari usually transcodes
to JPEG when the file input carries an `accept` allowlist, but not when a user shares from the
Files app. Set `accept="image/jpeg,image/png,image/webp"` on the input and let `validate_upload`
produce a clear Greek error otherwise. Adding `pillow-heif` later is a one-line optional upgrade.

### 4.3 Orphaned files

Django never deletes the underlying file when a `FileField` is replaced or its row is deleted,
and `file_overwrite = False` (§5) means every replacement writes a new key. With edit views now
in place, replacement is routine.

Add `django-cleanup` — it hooks `pre_save`/`post_delete` and removes the superseded object:

```python
INSTALLED_APPS = [
    ...,
    'django_cleanup.apps.CleanupConfig',   # must be LAST
]
```

Note a `catalog_reconcile_media` management command in the backlog as a safety net for anything
the signals miss (crash mid-save, manual DB edits). Not built in this pass.

---

## 5. S3 + CloudFront (greenfield)

### 5.1 AWS setup

Region: **eu-central-1** (Frankfurt) — closest major region to Greece. CloudFront makes the
origin region largely irrelevant to visitors, but keep the bucket near the VPS.

1. **S3 bucket** `opson-media`
   - **Block all public access: ON** (all four settings)
   - **Object Ownership: Bucket owner enforced** — this disables ACLs
2. **CloudFront distribution**
   - Origin: the bucket, using **Origin Access Control (OAC)**, not the legacy OAI
   - Viewer protocol policy: redirect HTTP → HTTPS
   - Note the distribution domain (`dxxxxxxxxxxxxx.cloudfront.net`) or attach
     `media.eopson.gr` with an ACM certificate **in us-east-1** (CloudFront only reads certs
     from that region — a common trip-up)
3. **Bucket policy** — grant only that distribution:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowCloudFrontServicePrincipalReadOnly",
    "Effect": "Allow",
    "Principal": { "Service": "cloudfront.amazonaws.com" },
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::opson-media/*",
    "Condition": {
      "StringEquals": {
        "AWS:SourceArn": "arn:aws:cloudfront::<ACCOUNT_ID>:distribution/<DISTRIBUTION_ID>"
      }
    }
  }]
}
```

4. **IAM user** for the app. The VPS is not EC2 (per `DEPLOY.md`), so there is no instance role
   to attach — static keys in `.env` are forced. Scope them tightly:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::opson-media/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::opson-media"
    }
  ]
}
```

Never `AmazonS3FullAccess`.

### 5.2 Django settings

```python
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'eu-central-1')
AWS_S3_CUSTOM_DOMAIN = os.environ.get('AWS_S3_CUSTOM_DOMAIN', '')   # CloudFront domain

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

if AWS_STORAGE_BUCKET_NAME:
    default_storage = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'bucket_name': AWS_STORAGE_BUCKET_NAME,
            'region_name': AWS_S3_REGION_NAME,
            'custom_domain': AWS_S3_CUSTOM_DOMAIN,
            'default_acl': None,          # bucket has ACLs disabled — see below
            'querystring_auth': False,    # CloudFront serves publicly via OAC
            'file_overwrite': False,
            'object_parameters': {'CacheControl': 'max-age=31536000, immutable'},
        },
    }
else:
    default_storage = {'BACKEND': 'django.core.files.storage.FileSystemStorage'}

STORAGES = {
    'default': default_storage,
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
```

> ### The gotcha that breaks this setup
> With **Object Ownership = bucket-owner-enforced**, S3 rejects any request carrying an ACL.
> `default_acl` **must be `None`**. Setting the intuitive `'public-read'` makes every single
> upload fail with `AccessControlListNotSupported`. This is the most common way this
> configuration goes wrong.

`file_overwrite = False` is what makes the one-year immutable `CacheControl` safe — every
version gets its own key, so CloudFront never serves a stale image.

Credentials come from `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` in the environment; boto3
picks them up without being told.

**Local development degrades to disk** when `AWS_STORAGE_BUCKET_NAME` is unset — rule 08:
*"An integration with unset credentials should degrade to an offline mode where possible, so the
app runs locally without them."*

### 5.3 Settings hardening (bundled)

`settings.py` is being edited anyway. The current fallback `SECRET_KEY` is a working key that has
been public in git since the initial commit:

```python
SECRET_KEY = os.environ['SECRET_KEY']            # crash on boot, never fail open
DEBUG = env_bool('DEBUG', False)                 # secure default
ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', [])
```

**Rotate the committed key** as part of this work. Behaviour change to communicate: a missing
`.env` now crashes on startup instead of silently starting in debug mode with `ALLOWED_HOSTS=['*']`
and every HSTS/SSL protection disabled.

### 5.4 `requirements.txt`

```
Django==5.1.4
gunicorn==23.0.0
whitenoise==6.8.2
python-dotenv==1.0.1
Pillow                     # image processing
django-storages[s3]        # S3 backend
boto3                      # AWS SDK
django-cleanup             # orphaned file removal
pytest                     # rule 10
pytest-django
```

**Remove `djangorestframework`** — it is in `requirements.txt` today but `rest_framework` is not
in `INSTALLED_APPS` and there is not a single serializer or API view in the project.

---

## 6. Seed → two management commands

`seed.py` must be rewritten regardless: it references `image_url`, `cover_url` and `role`, all of
which are going away. Two latent bugs to fix while rewriting.

**Bug 1 — it becomes permanently unrunnable.** `OrderItem.product` and `SubOrder.producer` are
both `PROTECT`, and `seed` opens with `Product.objects.all().delete()`. The moment one demo order
exists, re-running raises `ProtectedError`. (It fails atomically during collection, so nothing is
half-wiped — the `on_delete` choices are doing real work.)

**Bug 2 — an ordering trap once `role` is gone.** The cleanup filter
`User.objects.filter(role=PRODUCER)` becomes `User.objects.filter(producer_profile__isnull=False)`,
and that **must run before** `Producer.objects.all().delete()` — otherwise the profiles are
already gone, the filter matches nothing, and demo users are orphaned. Since `Producer.user` is
`CASCADE`, deleting the users cascades the producers anyway.

### `catalog_load_data` — idempotent, never deletes

Rule 11: reference data loads via a re-runnable `<app>_load_data`.

- Upserts on natural keys: `Category.slug`, `User.username`, `(producer, name)` for products
  — which is why §2.3 adds `unique_product_name_per_producer`
- Safe to run on the live demo at any time, including after orders exist
- `--dry-run` reports what would change
- Logs a final count

### `catalog_reset_demo` — destructive, guarded

- Deletes demo data in dependency order, users first
- **Refuses to run when any `Order` exists** unless passed `--force`
- `--dry-run`
- This is the only command that destroys anything

### Images in seed data

Both commands leave every `ImageField` **blank**. The 31 `loremflickr.com` URLs are dropped with
`image_url`. Templates already fall back to `{{ p.emoji|default:"🌾" }}` everywhere, so cards
render as emoji tiles.

> **Consequence to compensate for:** with no seeded images, the media pipeline gets **no
> end-to-end smoke test on deploy**. §8 therefore requires real unit tests on `render_variants`,
> and `DEPLOY.md` gains a manual verification step.

Also rename the `"Όλα"` handling comment — it stays a UI-only filter with no row, as today.

---

## 7. Views, templates, admin

### 7.1 Views

`producers/views.py` gains two views and all five use forms:

| View | Notes |
|---|---|
| `dashboard` | Unchanged behaviour; filter in the DB rather than Python list comprehensions |
| `transition_suborder` | Unchanged |
| `product_create` | Uses `ProductForm` |
| `product_update` | **New.** `get_object_or_404(Product, pk=pk, producer=producer)` |
| `profile_update` | **New.** Edits `request.user.producer_profile` |

The producer-scoping pattern (`get_object_or_404(..., producer=producer)`) is what prevents one
producer editing another's product. It must be present on both new views, and §8 requires a test
proving it.

`orders/views.py::checkout` uses `CheckoutForm` and gains the stock decrement:

```python
updated = (Product.objects
           .filter(pk=item['product'].pk, stock__gte=item['quantity'])
           .update(stock=F('stock') - item['quantity']))
if not updated:
    # someone took the last unit between validation and checkout
    raise InsufficientStock
```

A single conditional UPDATE — atomic at the database, no `select_for_update`, no services layer.
It goes inside the existing `transaction.atomic()` block. `InsufficientStock` lives in
`orders/exceptions.py` (a small new file; the full exception hierarchy is a later pass).

`cart/views.py` uses the cart forms. Delete `_back_or()` — it is an open redirect
(`redirect(request.META['HTTP_REFERER'])`); redirect to a named route instead.

### 7.2 Templates

| File | Change |
|---|---|
| `producers/product_form.html` | **Add `enctype="multipart/form-data"`** — without it the file never arrives. Replace the `image_url` text input with a file input carrying the `accept` allowlist |
| `catalog/home.html:79-80` | `p.cover_url` → `p.cover_card.url`, guarded by `{% if p.cover_card %}` |
| `catalog/product_detail.html:12-13` | → `product.image_detail.url` |
| `catalog/product_detail.html:81-82` | → `p.image_card.url` |
| `catalog/producer_detail.html` | cover → `cover_detail.url`; product grid → `image_card.url` |
| `cart/cart.html:29` | → `item.product.image_card.url` |
| `producers/dashboard.html` | Add an "edit" link per product to the new route |
| **all templates** | Every `{% url %}` updated to the kebab-case names from §2.5 |

Keep every existing emoji fallback branch — with seed leaving images blank, those branches are
now the common path, not the edge case.

### 7.3 Admin

Two rule-13 fixes worth taking while models are being rewritten:

```python
@register(SubOrder)
class SubOrderAdmin(ModelAdmin):
    """Sub-orders. Read-only: the state machine owns these rows."""
    list_select_related = ['order', 'producer']
    readonly_fields = [f.name for f in SubOrder._meta.fields]

    def has_add_permission(self, request) -> bool:
        return False
```

- **`readonly_fields`** closes a real hole: today staff can edit `status` directly in the admin,
  jumping `pending` → `delivered` and bypassing `SUBORDER_TRANSITIONS` entirely.
- **`list_select_related`** on `SubOrderAdmin` and `OrderAdmin` — their `list_display` renders
  related fields, so a 100-row changelist currently costs ~200 extra queries.

---

## 8. Testing

`pytest` + `pytest-django` (rule 10). Tests only for what this pass builds — the full rule-10
suite is a later pass.

**Constraints** (`orders/tests/`, `catalog/tests/`)
- `OrderItem(quantity=0)` and `quantity=-1` raise `IntegrityError`
- `Product(price=0)` raises `IntegrityError`
- Two `SubOrder`s for the same `(order, producer)` raise `IntegrityError`

**Forms**
- `CartAddForm` rejects `-100`, rejects `'abc'`, rejects quantity above `product.stock`
- `CheckoutForm` rejects a missing `address`
- `ProductForm` rejects an 9MB upload and a non-image file, with the Greek message

**Stock**
- Decrement reduces `stock` by the ordered quantity
- A second checkout for the last unit fails rather than overselling

**Images**
- `render_variants` returns both renditions at the right widths
- A portrait EXIF-rotated JPEG comes out upright
- Output carries no EXIF (assert GPS is gone)

**Access control** — mandatory per rule 06/10, non-negotiable on the two new views
- A producer gets 403/404 editing another producer's product
- A non-producer gets 403 on `producer-profile` and `producer-product-edit`

Docstrings state **why the test exists**, not what the code does (rule 10).

---

## 9. Explicitly out of scope

Do not do these in this pass:

- `services/` and `managers/` layers — checkout logic stays in the view for now
- Reels, Events and Reviews stay as hardcoded lists in `catalog/views.py`
- **Restocking on cancel** — returning stock when a `SubOrder` is cancelled puts a side effect
  into `transition_to`, which rule 01 forbids on a model method. Needs the services layer
- Payments / Stripe — its own project
- Postgres migration
- HTMX
- Celery
- A repo-wide style sweep (type hints, single quotes, `from django.db.models import ...`).
  **New and rewritten code follows the rules**; untouched files stay as they are, so the
  codebase will be mixed-style until that separate mechanical commit

**Known holes left open, to state honestly in the PR:**
- Overselling is closed, but stock is never *returned* on cancellation
- `SubOrder.transition_to` still raises a bare `ValueError` caught in a view (rule 09 wants an
  app exception the view never catches)
- There is still no logging anywhere in the project (rule 09)

---

## 10. Build order

1. `core/` app — `CreateUpdateDateModel`, `images.py`, `text.py`, with tests for `images.py`
2. `enums.py` in `orders`, `producers`, `catalog`
3. Models: constraints, `Meta`, field changes, drop `User.role` / `Product.slug` / `photo_url`
4. **Clean-slate migrations:** delete all eight existing migration files, delete `db.sqlite3`,
   then per app `python manage.py makemigrations <app> -n <descriptive_name>` (rule 11 —
   never leave a generator-default name like `0002_..._and_more`)
5. `settings.py`: `core` + `django_cleanup` in `INSTALLED_APPS`, media, `STORAGES`, hardening
6. `requirements.txt`
7. Forms in all four apps
8. Views rewritten onto forms; the two new producer views; stock decrement
9. URLs: `dashboard/` prefix, pk-prefixed producer detail, kebab-case names
10. Templates: `enctype`, file inputs, image fields, `{% url %}` renames
11. Admin: `readonly_fields`, `list_select_related`
12. `catalog_load_data` + `catalog_reset_demo`
13. Tests
14. `DEPLOY.md`: AWS env vars, renamed seed command, and a manual media check
    ("upload one product photo, confirm the object lands in the bucket and renders through
    CloudFront") — since seeded data no longer exercises the media path

### Branch

Per `terraweb2/CLAUDE.md`, never commit to `main`. Suggested:

```
catalog/none/CC/model-redesign-s3-media-forms
```

