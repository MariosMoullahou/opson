from django.contrib.admin import ModelAdmin, TabularInline, register
from django.http import HttpRequest

from orders.models import Order, OrderItem, SubOrder


class OrderItemInline(TabularInline):
    """Line items, shown on their sub-order."""

    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'unit', 'unit_price', 'quantity']


@register(SubOrder)
class SubOrderAdmin(ModelAdmin):
    """Sub-orders. Read-only: SUBORDER_TRANSITIONS owns these rows."""

    list_display = ['id', 'order', 'producer', 'status', 'subtotal', 'updated_at']
    list_filter = ['status', 'producer']
    search_fields = ['order__full_name', 'producer__farm_name']
    date_hierarchy = 'created_at'
    list_select_related = ['order', 'producer']
    inlines = [OrderItemInline]
    # Editing status here would jump the state machine straight from pending to delivered.
    readonly_fields = [field.name for field in SubOrder._meta.fields]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False


class SubOrderInline(TabularInline):
    """Sub-orders, shown on their parent order."""

    model = SubOrder
    extra = 0
    readonly_fields = ['producer', 'status', 'subtotal']
    show_change_link = True


@register(Order)
class OrderAdmin(ModelAdmin):
    """Customer orders."""

    list_display = ['id', 'customer', 'full_name', 'phone', 'total', 'created_at']
    list_filter = ['created_at']
    search_fields = ['full_name', 'phone', 'customer__username']
    date_hierarchy = 'created_at'
    list_select_related = ['customer']
    inlines = [SubOrderInline]
    readonly_fields = ['total', 'created_at', 'updated_at']
