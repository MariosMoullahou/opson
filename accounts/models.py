from django.contrib.auth.models import AbstractUser
from django.db.models import CharField


class User(AbstractUser):
    """A marketplace account; the ones carrying a producer_profile are producers."""

    phone = CharField(max_length=32, blank=True, default='')

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    @property
    def is_producer(self) -> bool:
        return hasattr(self, 'producer_profile')
