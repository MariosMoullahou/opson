from decimal import Decimal

from django.conf import settings
from django.db import models

from catalog.models import Product
from producers.models import Producer


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    PREPARING = "preparing", "Preparing"
    READY = "ready", "Ready"
    OUT_FOR_DELIVERY = "out_for_delivery", "Out for delivery"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"


SUBORDER_TRANSITIONS = {
    OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
    OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
    OrderStatus.PREPARING: [OrderStatus.READY, OrderStatus.CANCELLED],
    OrderStatus.READY: [OrderStatus.OUT_FOR_DELIVERY],
    OrderStatus.OUT_FOR_DELIVERY: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [],
    OrderStatus.CANCELLED: [],
}


class Order(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32)
    address = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} - {self.full_name}"

    @property
    def aggregate_status(self):
        statuses = list(self.sub_orders.values_list("status", flat=True))
        if not statuses:
            return OrderStatus.PENDING
        if all(s == OrderStatus.DELIVERED for s in statuses):
            return OrderStatus.DELIVERED
        if all(s == OrderStatus.CANCELLED for s in statuses):
            return OrderStatus.CANCELLED
        priority = [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PREPARING,
            OrderStatus.READY,
            OrderStatus.OUT_FOR_DELIVERY,
        ]
        for p in priority:
            if p in statuses:
                return p
        return OrderStatus.PENDING

    def recalculate_total(self):
        total = sum((so.subtotal for so in self.sub_orders.all()), Decimal("0.00"))
        self.total = total
        self.save(update_fields=["total"])


class SubOrder(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="sub_orders")
    producer = models.ForeignKey(Producer, on_delete=models.PROTECT, related_name="sub_orders")
    status = models.CharField(
        max_length=24, choices=OrderStatus.choices, default=OrderStatus.PENDING
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("order", "producer")]
        ordering = ["-order__created_at"]

    def __str__(self):
        return f"SubOrder #{self.pk} - {self.producer.farm_name} ({self.get_status_display()})"

    def allowed_next_statuses(self):
        return SUBORDER_TRANSITIONS.get(OrderStatus(self.status), [])

    def can_transition_to(self, new_status):
        return new_status in self.allowed_next_statuses()

    def transition_to(self, new_status):
        new_status = OrderStatus(new_status)
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])

    def recalculate_subtotal(self):
        total = sum((item.line_total for item in self.items.all()), Decimal("0.00"))
        self.subtotal = total
        self.save(update_fields=["subtotal", "updated_at"])


class OrderItem(models.Model):
    sub_order = models.ForeignKey(SubOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=140)
    unit = models.CharField(max_length=16)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"
