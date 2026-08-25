from decimal import Decimal

import pytest

from core.images import MAX_UPLOAD_BYTES
from core.tests.factories import a_text_file, an_image_file
from producers.forms import ProductForm
from producers.tests.factories import a_producer

pytestmark = pytest.mark.django_db

VALID_PRODUCT = {
    'name': 'Θυμαρίσιο Μέλι',
    'description': 'Αφιλτράριστο.',
    'category': '',
    'unit': 'jar',
    'unit_label': '450γρ',
    'price': Decimal('7.50'),
    'stock': 10,
    'emoji': '🍯',
    'is_active': True,
}


def test_an_oversized_upload_is_rejected_in_greek():
    """A producer on a phone needs to know to shrink the photo, not read a Django stack trace."""
    upload = an_image_file()
    upload.size = MAX_UPLOAD_BYTES + 1

    form = ProductForm(VALID_PRODUCT, {'image': upload})

    assert not form.is_valid()
    assert 'πολύ μεγάλη' in form.errors['image'][0]


def test_a_non_image_upload_is_rejected_in_greek():
    """A renamed .txt used to reach Pillow and surface as a 500."""
    form = ProductForm(VALID_PRODUCT, {'image': a_text_file()})

    assert not form.is_valid()
    assert 'εικόνα' in form.errors['image'][0]


def test_a_valid_upload_fills_both_renditions():
    """One upload has to populate both fields, or the detail page falls back to an emoji tile."""
    form = ProductForm(VALID_PRODUCT, {'image': an_image_file()})
    assert form.is_valid(), form.errors

    product = form.save(commit=False)
    product.producer = a_producer()
    product.save()

    assert product.image_card.name.startswith('products/')
    assert product.image_detail.name.startswith('products/')
    assert product.image_card.name != product.image_detail.name


def test_a_product_saves_without_any_upload():
    """The image is optional; the emoji fallback is the common path while seed data has no photos."""
    form = ProductForm(VALID_PRODUCT, {})
    assert form.is_valid(), form.errors

    product = form.save(commit=False)
    product.producer = a_producer()
    product.save()

    assert not product.image_card


def test_the_producer_is_not_a_form_field():
    """A producer field would let one producer post another producer's id and write to their catalog."""
    assert 'producer' not in ProductForm().fields
