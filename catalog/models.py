from uuid import uuid4

from django.db.models import (
    CASCADE,
    SET_NULL,
    BooleanField,
    CharField,
    CheckConstraint,
    DecimalField,
    ForeignKey,
    ImageField,
    Index,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    Q,
    SlugField,
    TextField,
    UniqueConstraint,
)

from catalog.enums import ProductUnit
from core.models import CreateUpdateDateModel
from core.text import greek_slug
from producers.models import Producer


def product_image_path(instance: 'Product', filename: str) -> str:
    """A UUID key keeps Greek filenames, and the original filename, out of the bucket."""
    return f'products/{uuid4()}.webp'


class Category(CreateUpdateDateModel):
    """A top-level grouping shown in the category nav."""

    name = CharField(max_length=80, unique=True)
    slug = SlugField(max_length=100, unique=True, blank=True, default='', allow_unicode=True)
    emoji = CharField(max_length=8, blank=True, default='')
    sort_order = PositiveSmallIntegerField(default=100)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = greek_slug(self.name)
        super().save(*args, **kwargs)


class Product(CreateUpdateDateModel):
    """Something a producer sells, priced per unit."""

    producer = ForeignKey(Producer, on_delete=CASCADE, related_name='products')
    category = ForeignKey(Category, on_delete=SET_NULL, null=True, blank=True, related_name='products')
    name = CharField(max_length=140)
    description = TextField(blank=True, default='')
    unit = CharField(max_length=16, choices=ProductUnit.choices, default=ProductUnit.PIECE)
    unit_label = CharField(
        max_length=24,
        blank=True,
        default='',
        help_text="Optional display label e.g. '500γρ', '750ml'",
    )
    price = DecimalField(max_digits=8, decimal_places=2)
    stock = PositiveIntegerField(default=0)
    image_card = ImageField(upload_to=product_image_path, blank=True)
    image_detail = ImageField(upload_to=product_image_path, blank=True)
    emoji = CharField(max_length=8, blank=True, default='', help_text='Fallback shown when no image is uploaded.')
    is_active = BooleanField(default=True)
    agroverify_code = CharField(
        max_length=64,
        blank=True,
        default='',
        help_text=(
            'Μοναδικός κωδικός Agro-Verify ανά παρτίδα (κρατικό σύστημα ιχνηλασιμότητας ΥΠΨηΔ/ΥΠΑΑΤ). '
            'Άδειο όσο το API δεν είναι ακόμη διαθέσιμο.'
        ),
    )

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        constraints = [
            CheckConstraint(condition=Q(price__gt=0), name='product_price_positive'),
            UniqueConstraint(fields=['producer', 'name'], name='unique_product_name_per_producer'),
        ]
        indexes = [Index(fields=['is_active']), Index(fields=['producer', 'is_active'])]

    def __str__(self) -> str:
        return f'{self.name} - {self.producer.farm_name}'
