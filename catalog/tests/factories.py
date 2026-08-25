from decimal import Decimal

from catalog.enums import ProductUnit
from catalog.models import Category, Product
from producers.models import Producer
from producers.tests.factories import a_producer


def a_category(*, name: str = 'Μέλι', **fields) -> Category:
    """A saved category; the slug fills itself in on save."""
    return Category.objects.create(name=name, **fields)


def a_product(*, producer: Producer | None = None, name: str = 'Θυμαρίσιο Μέλι', **fields) -> Product:
    """A saved, in-stock, active product."""
    producer = producer or a_producer()
    fields.setdefault('price', Decimal('7.50'))
    fields.setdefault('stock', 10)
    fields.setdefault('unit', ProductUnit.JAR)
    return Product.objects.create(producer=producer, name=name, **fields)
