import pytest

from catalog.tests.factories import a_product
from producers.tests.factories import DEFAULT_PASSWORD, a_producer, a_user

pytestmark = pytest.mark.django_db

PROFILE_URL = '/dashboard/profile/'
DASHBOARD_URL = '/dashboard/'


def _sign_in(client, user) -> None:
    client.login(username=user.username, password=DEFAULT_PASSWORD)


def test_a_producer_cannot_open_another_producers_product(client):
    """Scoping the lookup by producer is the only thing standing between one farm and another's catalog."""
    victim_product = a_product(producer=a_producer(username='victim'))
    intruder = a_producer(username='intruder')
    _sign_in(client, intruder.user)

    response = client.get(f'/dashboard/products/{victim_product.pk}/edit/')

    assert response.status_code == 404


def test_a_producer_cannot_post_edits_to_another_producers_product(client):
    """A GET that 404s is not enough; the POST path must be scoped too."""
    victim_product = a_product(producer=a_producer(username='victim'), name='Πριν')
    intruder = a_producer(username='intruder')
    _sign_in(client, intruder.user)

    client.post(f'/dashboard/products/{victim_product.pk}/edit/', {'name': 'Μετά', 'price': '1.00', 'stock': '1'})

    victim_product.refresh_from_db()
    assert victim_product.name == 'Πριν'


def test_a_customer_cannot_reach_the_producer_profile_page(client):
    """A signed-in customer has no producer_profile; the view must refuse rather than crash on the relation."""
    _sign_in(client, a_user(username='shopper'))

    assert client.get(PROFILE_URL).status_code == 404


def test_a_customer_cannot_reach_a_product_edit_page(client):
    """Same guard on the other new view."""
    product = a_product(producer=a_producer(username='owner'))
    _sign_in(client, a_user(username='shopper'))

    assert client.get(f'/dashboard/products/{product.pk}/edit/').status_code == 404


def test_an_anonymous_visitor_is_sent_to_login(client):
    """login_required has to come before the producer check, or anonymous users hit the relation lookup."""
    response = client.get(DASHBOARD_URL)

    assert response.status_code == 302
    assert '/accounts/login/' in response['Location']
