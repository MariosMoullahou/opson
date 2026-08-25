import pytest

from cart.forms import CartAddForm, CartUpdateForm
from catalog.tests.factories import a_product

pytestmark = pytest.mark.django_db


def test_a_negative_quantity_is_rejected():
    """quantity=-100 reached the cart untouched and produced a -887.50 order total."""
    form = CartAddForm({'quantity': -100}, product=a_product())

    assert not form.is_valid()


def test_a_non_numeric_quantity_is_rejected():
    """int('abc') raised straight out of the view as a 500; the form turns it into a field error."""
    form = CartAddForm({'quantity': 'abc'}, product=a_product())

    assert not form.is_valid()


def test_a_quantity_above_stock_is_rejected():
    """Adding more than exists lets a customer reach checkout for goods the producer cannot ship."""
    form = CartAddForm({'quantity': 5}, product=a_product(stock=3))

    assert not form.is_valid()
    assert 'απόθεμα' in form.errors['quantity'][0]


def test_a_quantity_within_stock_is_accepted():
    """The ordinary case still has to pass, stock check included."""
    form = CartAddForm({'quantity': 3}, product=a_product(stock=3))

    assert form.is_valid()


def test_zero_is_rejected_on_add_but_accepted_on_update():
    """Zero means 'remove this line', which is meaningful on update and meaningless on add."""
    product = a_product(stock=5)

    assert not CartAddForm({'quantity': 0}, product=product).is_valid()
    assert CartUpdateForm({'quantity': 0}, product=product).is_valid()
