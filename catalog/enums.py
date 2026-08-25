from django.db.models import TextChoices


class ProductUnit(TextChoices):
    """The unit a product's price is quoted in."""

    KG = 'kg', 'kg'
    PIECE = 'piece', 'piece'
    BUNCH = 'bunch', 'bunch'
    LITER = 'liter', 'liter'
    JAR = 'jar', 'jar'
