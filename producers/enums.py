from django.db.models import TextChoices


class ProducerBadge(TextChoices):
    """The provenance claim shown on a producer's card."""

    BIO = 'bio', 'Βιολογικό'
    TRADITIONAL = 'traditional', 'Παραδοσιακό'
    PDO = 'pdo', 'ΠΟΠ'
