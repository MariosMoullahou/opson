
from django.contrib.auth import get_user_model

from producers.models import Producer

User = get_user_model()

DEFAULT_PASSWORD = 'test-pass-1234'


def a_user(*, username: str = 'someone', **fields) -> User:
    """A saved account with a usable password."""
    return User.objects.create_user(username=username, password=DEFAULT_PASSWORD, **fields)


def a_producer(*, user: User | None = None, farm_name: str = 'Κτήμα Δοκιμής', **fields) -> Producer:
    """A saved producer with its own account."""
    user = user or a_user(username=fields.pop('username', f'producer-{Producer.objects.count()}'))
    return Producer.objects.create(user=user, farm_name=farm_name, **fields)
