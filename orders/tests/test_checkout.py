from decimal import Decimal

import pytest

from catalog.models import Product
from catalog.tests.factories import a_product
from orders.models import Order
from producers.tests.factories import DEFAULT_PASSWORD, a_user

pytestmark = pytest.mark.django_db

CHECKOUT_URL = '/orders/checkout/'
DELIVERY = {'full_name': 'Μαρία Κ.', 'phone': '+30 210 1234567', 'address': 'Ερμού 1, Αθήνα', 'notes': ''}


def _signed_in_client(client):
    user = a_user(username='buyer')
    client.login(username=user.username, password=DEFAULT_PASSWORD)
    return client


def _cart(client, product: Product, quantity: int) -> None:
    session = client.session
    session['cart'] = {str(product.pk): quantity}
    session.save()


def test_checkout_decrements_stock_by_the_ordered_quantity(client):
    """Without this the catalog never runs out and producers get orders they cannot fill."""
    product = a_product(stock=10)
    client = _signed_in_client(client)
    _cart(client, product, 3)

    client.post(CHECKOUT_URL, DELIVERY)

    product.refresh_from_db()
    assert product.stock == 7


def test_checkout_for_the_last_unit_fails_rather_than_overselling(client):
    """Two customers racing for one jar must not both get it; the conditional UPDATE is the guard."""
    product = a_product(stock=1)
    client = _signed_in_client(client)
    _cart(client, product, 2)

    client.post(CHECKOUT_URL, DELIVERY)

    product.refresh_from_db()
    assert product.stock == 1
    assert not Order.objects.exists()


def test_a_missing_address_does_not_create_an_order(client):
    """Order.objects.create used to bypass validators, producing orders with an empty delivery address."""
    product = a_product()
    client = _signed_in_client(client)
    _cart(client, product, 1)

    client.post(CHECKOUT_URL, {**DELIVERY, 'address': ''})

    assert not Order.objects.exists()


def test_a_successful_checkout_totals_the_cart(client):
    """The total is what the customer is charged; an unsummed order is a silent billing error."""
    product = a_product(price=Decimal('7.50'), stock=5)
    client = _signed_in_client(client)
    _cart(client, product, 2)

    client.post(CHECKOUT_URL, DELIVERY)

    assert Order.objects.get().total == Decimal('15.00')
