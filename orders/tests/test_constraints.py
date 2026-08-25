from decimal import Decimal

import pytest
from django.db.utils import IntegrityError

from orders.tests.factories import a_sub_order, an_order, an_order_item
from producers.tests.factories import a_producer

pytestmark = pytest.mark.django_db


def test_a_zero_quantity_line_cannot_be_saved():
    """A zero-quantity line contributes nothing but still shows in the order, confusing the producer."""
    with pytest.raises(IntegrityError):
        an_order_item(quantity=0)


def test_a_negative_quantity_line_cannot_be_saved():
    """This is the -100 bug: a negative quantity drove the order total to -887.50."""
    with pytest.raises(IntegrityError):
        an_order_item(quantity=-1)


def test_a_negative_unit_price_cannot_be_saved():
    """A negative snapshot price would subtract from the subtotal even with a positive quantity."""
    with pytest.raises(IntegrityError):
        an_order_item(unit_price=Decimal('-1.00'))


def test_one_producer_gets_one_sub_order_per_order():
    """Two sub-orders for the same producer would split their basket across two dashboard cards."""
    order = an_order()
    producer = a_producer()
    a_sub_order(order=order, producer=producer)

    with pytest.raises(IntegrityError):
        a_sub_order(order=order, producer=producer)
