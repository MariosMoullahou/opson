from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from catalog.models import Category, Product
from orders.models import Order
from producers.models import Producer

User = get_user_model()


class _DryRun(Exception):
    """Raised to roll the transaction back once a dry run has counted everything."""


class Command(BaseCommand):
    help = 'Destroy the Opson demo catalog. The only command in the project that deletes anything.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--dry-run', action='store_true', help='Report what would be deleted, then roll back.')
        parser.add_argument('--force', action='store_true', help='Delete even when real orders exist.')

    def handle(self, *args, **options) -> None:
        dry_run = options['dry_run']
        order_count = Order.objects.count()
        if order_count and not options['force']:
            raise CommandError(f'{order_count} order(s) exist. Re-run with --force to destroy them too.')

        try:
            with transaction.atomic():
                deleted = self._reset(delete_orders=bool(order_count))
                if dry_run:
                    raise _DryRun
        except _DryRun:
            self.stdout.write(self.style.WARNING('Dry run — nothing was deleted.'))

        for label, count in deleted.items():
            self.stdout.write(f'{label:12} deleted {count:3}')

    def _reset(self, *, delete_orders: bool) -> dict[str, int]:
        deleted = {}

        if delete_orders:
            # OrderItem.product and SubOrder.producer are PROTECT, so orders block everything below.
            deleted['orders'], _ = Order.objects.all().delete()

        # Producer.user is CASCADE, so this must run before the producers are gone or it matches nothing.
        deleted['users'], _ = User.objects.filter(producer_profile__isnull=False).delete()
        deleted['producers'], _ = Producer.objects.all().delete()
        deleted['products'], _ = Product.objects.all().delete()
        deleted['categories'], _ = Category.objects.all().delete()
        return deleted
