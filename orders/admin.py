from django.contrib import admin

from .models import Order, OrderItem, SubOrder


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "unit", "unit_price", "quantity")


@admin.register(SubOrder)
class SubOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "producer", "status", "subtotal", "updated_at")
    list_filter = ("status", "producer")
    inlines = [OrderItemInline]


class SubOrderInline(admin.TabularInline):
    model = SubOrder
    extra = 0
    readonly_fields = ("producer", "status", "subtotal")
    show_change_link = True


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "full_name", "total", "created_at")
    search_fields = ("full_name", "customer__username")
    inlines = [SubOrderInline]
    date_hierarchy = "created_at"
