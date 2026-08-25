from decimal import Decimal

from django.conf import settings
from django.db.models import (
    CASCADE,
    PROTECT,
    CharField,
    CheckConstraint,
    DecimalField,
    ForeignKey,
    Index,
    PositiveIntegerField,
    Q,
    TextField,
    UniqueConstraint,
)

from catalog.models import Product
from core.models import CreateUpdateDateModel
from orders.enums import SUBORDER_TRANSITIONS, OrderStatus
from producers.models import Producer

_AGGREGATE_STATUS_PRIORITY = [
    OrderStatus.PENDING,
    OrderStatus.CONFIRMED,
    OrderStatus.PREPARING,
    OrderStatus.READY,
    OrderStatus.OUT_FOR_DELIVERY,
]


class Order(CreateUpdateDateModel):
    """One customer checkout, split into a sub-order per producer."""

    customer = ForeignKey(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name='orders')
    full_name = CharField(max_length=120)
    phone = CharField(max_length=32)
    address = CharField(max_length=255)
    notes = TextField(blank=True, default='')
    total = DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [Index(fields=['customer', 'created_at'])]

    def __str__(self) -> str:
        return f'Order #{self.pk} - {self.full_name}'

    @property
    def aggregate_status(self) -> OrderStatus:
        """The single status shown to the customer for an order spanning several producers."""
        statuses = list(self.sub_orders.values_list('status', flat=True))
        if not statuses:
            return OrderStatus.PENDING
        if all(s == OrderStatus.DELIVERED for s in statuses):
            return OrderStatus.DELIVERED
        if all(s == OrderStatus.CANCELLED for s in statuses):
            return OrderStatus.CANCELLED
        for status in _AGGREGATE_STATUS_PRIORITY:
            if status in statuses:
                return status
        return OrderStatus.PENDING

    def recalculate_total(self) -> None:
        """Re-sum this order from its sub-orders."""
        self.total = sum((so.subtotal for so in self.sub_orders.all()), Decimal('0.00'))
        self.save(update_fields=['total', 'updated_at'])


class SubOrder(CreateUpdateDateModel):
    """The part of an order belonging to one producer, with its own fulfilment status."""

    order = ForeignKey(Order, on_delete=CASCADE, related_name='sub_orders')
    producer = ForeignKey(Producer, on_delete=PROTECT, related_name='sub_orders')
    status = CharField(max_length=24, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    subtotal = DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = 'Sub Order'
        verbose_name_plural = 'Sub Orders'
        ordering = ['-order__created_at']
        constraints = [
            UniqueConstraint(fields=['order', 'producer'], name='unique_suborder_per_producer'),
        ]
        indexes = [Index(fields=['status']), Index(fields=['producer', 'status'])]

    def __str__(self) -> str:
        return f'SubOrder #{self.pk} - {self.producer.farm_name} ({self.get_status_display()})'

    def allowed_next_statuses(self) -> list[OrderStatus]:
        """The statuses this sub-order may move to from where it is now."""
        return SUBORDER_TRANSITIONS.get(OrderStatus(self.status), [])

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in self.allowed_next_statuses()

    def transition_to(self, new_status: str) -> None:
        """Move this sub-order one step along its fulfilment pipeline."""
        new_status = OrderStatus(new_status)
        if not self.can_transition_to(new_status):
            raise ValueError(f'Cannot transition from {self.status} to {new_status}')
        self.status = new_status
        self.save(update_fields=['status', 'updated_at'])

    def recalculate_subtotal(self) -> None:
        """Re-sum this sub-order from its items."""
        self.subtotal = sum((item.line_total for item in self.items.all()), Decimal('0.00'))
        self.save(update_fields=['subtotal', 'updated_at'])


class OrderItem(CreateUpdateDateModel):
    """One product line, with name and price copied so history survives catalog edits."""

    sub_order = ForeignKey(SubOrder, on_delete=CASCADE, related_name='items')
    product = ForeignKey(Product, on_delete=PROTECT, related_name='order_items')
    product_name = CharField(max_length=140)
    unit = CharField(max_length=16)
    unit_price = DecimalField(max_digits=8, decimal_places=2)
    quantity = PositiveIntegerField()

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        constraints = [
            CheckConstraint(condition=Q(quantity__gt=0), name='orderitem_quantity_positive'),
            CheckConstraint(condition=Q(unit_price__gte=0), name='orderitem_unit_price_non_negative'),
        ]

    def __str__(self) -> str:
        return f'{self.quantity} x {self.product_name}'

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity
