from decimal import Decimal

import pytest
from django.db.utils import IntegrityError

from producers.tests.factories import a_producer

pytestmark = pytest.mark.django_db


def test_a_rating_above_five_cannot_be_saved():
    """Ratings drive the star display, which renders 5 - int(rating) empty stars and would go negative."""
    with pytest.raises(IntegrityError):
        a_producer(rating=Decimal('5.1'))


def test_a_negative_rating_cannot_be_saved():
    """A negative rating would render a negative number of full stars."""
    with pytest.raises(IntegrityError):
        a_producer(rating=Decimal('-0.1'))


def test_a_greek_farm_name_produces_a_non_empty_slug():
    """Greek slugs are why lookups moved to pk; an empty slug would still make every URL collide."""
    assert a_producer(farm_name='Μπαρμπαγιάννης Κτήμα').slug != ''
