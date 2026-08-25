from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from catalog.demo_data import ALL_CATEGORIES_SLUG, CATEGORIES, DEMO_EMAIL_DOMAIN, DEMO_PASSWORD, PRODUCERS
from catalog.models import Category, Product
from producers.models import Producer

User = get_user_model()


class _DryRun(Exception):
    """Raised to roll the transaction back once a dry run has counted everything."""


class Command(BaseCommand):
    help = 'Load the Opson demo catalog. Idempotent: upserts on natural keys and never deletes.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--dry-run', action='store_true', help='Report what would change, then roll back.')

    def handle(self, *args, **options) -> None:
        dry_run = options['dry_run']
        try:
            with transaction.atomic():
                created, updated = self._load()
                if dry_run:
                    raise _DryRun
        except _DryRun:
            self.stdout.write(self.style.WARNING('Dry run — nothing was written.'))

        for label in ('categories', 'producers', 'products', 'users'):
            self.stdout.write(f'{label:12} created {created[label]:3}  updated {updated[label]:3}')
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'Demo logins use password: {DEMO_PASSWORD}'))

    def _load(self) -> tuple[dict[str, int], dict[str, int]]:
        created = dict.fromkeys(('categories', 'producers', 'products', 'users'), 0)
        updated = dict.fromkeys(('categories', 'producers', 'products', 'users'), 0)

        category_by_name = {}
        for name, slug, emoji, sort_order in CATEGORIES:
            if slug == ALL_CATEGORIES_SLUG:
                continue
            category, was_created = Category.objects.update_or_create(
                slug=slug,
                defaults={'name': name, 'emoji': emoji, 'sort_order': sort_order},
            )
            category_by_name[name] = category
            created['categories'] += was_created
            updated['categories'] += not was_created

        for entry in PRODUCERS:
            user, was_created = User.objects.get_or_create(
                username=entry['username'],
                defaults={'email': f'{entry["username"]}@{DEMO_EMAIL_DOMAIN}'},
            )
            if was_created:
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=['password'])
            created['users'] += was_created
            updated['users'] += not was_created

            producer, was_created = Producer.objects.update_or_create(
                user=user,
                defaults={
                    'farm_name': entry['farm_name'],
                    'village': entry['village'],
                    'region': entry['region'],
                    'badge': entry['badge'],
                    'rating': Decimal(entry['rating']),
                    'rating_count': entry['rating_count'],
                    'bio': entry['bio'],
                },
            )
            created['producers'] += was_created
            updated['producers'] += not was_created

            for category_name, name, unit, unit_label, price, stock, emoji, description in entry['products']:
                _, was_created = Product.objects.update_or_create(
                    producer=producer,
                    name=name,
                    defaults={
                        'category': category_by_name.get(category_name),
                        'unit': unit,
                        'unit_label': unit_label,
                        'price': Decimal(price),
                        'stock': stock,
                        'emoji': emoji,
                        'description': description,
                    },
                )
                created['products'] += was_created
                updated['products'] += not was_created

        customer, was_created = User.objects.get_or_create(
            username='customer',
            defaults={'email': f'customer@{DEMO_EMAIL_DOMAIN}'},
        )
        if was_created:
            customer.set_password(DEMO_PASSWORD)
            customer.save(update_fields=['password'])
        created['users'] += was_created
        updated['users'] += not was_created

        return created, updated
