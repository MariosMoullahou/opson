from decimal import Decimal

import pytest
from django.db.utils import IntegrityError

from catalog.models import Product
from catalog.tests.factories import a_category, a_product
from producers.tests.factories import a_producer

pytestmark = pytest.mark.django_db


def test_a_free_product_cannot_be_saved():
    """A zero price silently zeroes an order total; the database is the only layer that always sees it."""
    with pytest.raises(IntegrityError):
        a_product(price=Decimal('0.00'))


def test_a_negative_price_cannot_be_saved():
    """A negative price would let a cart line subtract from the order total."""
    with pytest.raises(IntegrityError):
        a_product(price=Decimal('-1.00'))


def test_one_producer_cannot_list_the_same_product_name_twice():
    """catalog_load_data upserts on (producer, name); without uniqueness a re-run duplicates the catalog."""
    producer = a_producer()
    a_product(producer=producer, name='Θυμαρίσιο Μέλι')

    with pytest.raises(IntegrityError):
        a_product(producer=producer, name='Θυμαρίσιο Μέλι')


def test_two_producers_may_share_a_product_name():
    """Uniqueness is per producer — two farms both selling honey is the normal case."""
    a_product(producer=a_producer(username='first'), name='Θυμαρίσιο Μέλι')
    a_product(producer=a_producer(username='second'), name='Θυμαρίσιο Μέλι')

    assert Product.objects.filter(name='Θυμαρίσιο Μέλι').count() == 2


def test_a_greek_category_name_produces_a_non_empty_slug():
    """ASCII slugify erases Greek entirely, which would give every category the same empty slug."""
    assert a_category(name='Ελαιόλαδο').slug != ''
