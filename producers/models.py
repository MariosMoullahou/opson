from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Producer(models.Model):
    class Badge(models.TextChoices):
        BIO = "bio", "Βιολογικό"
        TRADITIONAL = "traditional", "Παραδοσιακό"
        PDO = "pdo", "ΠΟΠ"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="producer_profile",
    )
    farm_name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    village = models.CharField(max_length=120, blank=True)
    region = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    photo_url = models.URLField(blank=True, max_length=500)
    cover_url = models.URLField(blank=True, max_length=500)
    badge = models.CharField(max_length=20, choices=Badge.choices, blank=True)
    agroverify_id = models.CharField(
        max_length=32,
        blank=True,
        help_text="Εθνικός κωδικός εγγραφής στο σύστημα Agro-Verify (ΥΠΨηΔ/ΥΠΑΑΤ). Άδειο όσο το API δεν είναι ακόμη διαθέσιμο — εμφανίζεται badge 'Ready'.",
    )
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    rating_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def location(self):
        if self.village and self.region:
            return f"{self.village}, {self.region}"
        return self.village or self.region

    @property
    def stars_full(self):
        return int(self.rating)

    @property
    def stars_empty(self):
        return 5 - int(self.rating)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.farm_name, allow_unicode=True) or self.user.username
            slug = base
            i = 2
            while Producer.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.farm_name
