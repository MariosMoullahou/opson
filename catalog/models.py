from django.db import models
from django.utils.text import slugify

from producers.models import Producer


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    emoji = models.CharField(max_length=8, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=100)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["sort_order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    class Unit(models.TextChoices):
        KG = "kg", "kg"
        PIECE = "piece", "piece"
        BUNCH = "bunch", "bunch"
        LITER = "liter", "liter"
        JAR = "jar", "jar"

    producer = models.ForeignKey(Producer, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    name = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=16, choices=Unit.choices, default=Unit.PIECE)
    unit_label = models.CharField(max_length=24, blank=True, help_text="Optional display label e.g. '500γρ', '750ml'")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image_url = models.URLField(blank=True, max_length=500)
    emoji = models.CharField(max_length=8, blank=True)
    is_active = models.BooleanField(default=True)
    agroverify_code = models.CharField(
        max_length=64,
        blank=True,
        help_text="Μοναδικός κωδικός Agro-Verify ανά παρτίδα (κρατικό σύστημα ιχνηλασιμότητας ΥΠΨηΔ/ΥΠΑΑΤ). Άδειο όσο το API δεν είναι ακόμη διαθέσιμο.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.producer.farm_name}-{self.name}", allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.producer.farm_name}"
