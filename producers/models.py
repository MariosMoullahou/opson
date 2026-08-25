from uuid import uuid4

from django.conf import settings
from django.db.models import (
    CASCADE,
    CharField,
    CheckConstraint,
    DecimalField,
    ImageField,
    OneToOneField,
    PositiveIntegerField,
    Q,
    SlugField,
    TextField,
)

from core.models import CreateUpdateDateModel
from core.text import greek_slug
from producers.enums import ProducerBadge

MAX_RATING = 5


def producer_cover_path(instance: 'Producer', filename: str) -> str:
    """A UUID key keeps Greek filenames, and the original filename, out of the bucket."""
    return f'producers/{uuid4()}.webp'


class Producer(CreateUpdateDateModel):
    """A farm or workshop selling on the marketplace."""

    user = OneToOneField(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='producer_profile')
    farm_name = CharField(max_length=120)
    slug = SlugField(
        max_length=140,
        blank=True,
        default='',
        allow_unicode=True,
        help_text='Decorative only — URLs resolve by pk.',
    )
    village = CharField(max_length=120, blank=True, default='')
    region = CharField(max_length=120, blank=True, default='')
    bio = TextField(blank=True, default='')
    cover_card = ImageField(upload_to=producer_cover_path, blank=True)
    cover_detail = ImageField(upload_to=producer_cover_path, blank=True)
    badge = CharField(max_length=20, choices=ProducerBadge.choices, blank=True, default='')
    agroverify_id = CharField(
        max_length=32,
        blank=True,
        default='',
        help_text=(
            'Εθνικός κωδικός εγγραφής στο σύστημα Agro-Verify (ΥΠΨηΔ/ΥΠΑΑΤ). '
            'Άδειο όσο το API δεν είναι ακόμη διαθέσιμο — εμφανίζεται badge "Ready".'
        ),
    )
    rating = DecimalField(max_digits=3, decimal_places=1, default=0)
    rating_count = PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Producer'
        verbose_name_plural = 'Producers'
        constraints = [
            CheckConstraint(condition=Q(rating__gte=0) & Q(rating__lte=MAX_RATING), name='producer_rating_range'),
        ]

    def __str__(self) -> str:
        return self.farm_name

    @property
    def location(self) -> str:
        if self.village and self.region:
            return f'{self.village}, {self.region}'
        return self.village or self.region

    @property
    def stars_full(self) -> int:
        return int(self.rating)

    @property
    def stars_empty(self) -> int:
        return MAX_RATING - int(self.rating)

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = greek_slug(self.farm_name)
        super().save(*args, **kwargs)
