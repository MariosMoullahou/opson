from collections import defaultdict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from cart.cart import Cart

from .models import Order, OrderItem, SubOrder


@login_required
def checkout(request):
    cart = Cart(request)
    if not cart.data:
        return redirect("cart")

    if request.method == "POST":
        with transaction.atomic():
            order = Order.objects.create(
                customer=request.user,
                full_name=request.POST.get("full_name", request.user.get_full_name() or request.user.username),
                phone=request.POST.get("phone", ""),
                address=request.POST.get("address", ""),
                notes=request.POST.get("notes", ""),
            )

            grouped = defaultdict(list)
            for item in cart.items():
                grouped[item["product"].producer].append(item)

            order_total = Decimal("0.00")
            for producer, items in grouped.items():
                sub = SubOrder.objects.create(order=order, producer=producer)
                subtotal = Decimal("0.00")
                for item in items:
                    p = item["product"]
                    OrderItem.objects.create(
                        sub_order=sub,
                        product=p,
                        product_name=p.name,
                        unit=p.unit,
                        unit_price=p.price,
                        quantity=item["quantity"],
                    )
                    subtotal += p.price * item["quantity"]
                sub.subtotal = subtotal
                sub.save(update_fields=["subtotal"])
                order_total += subtotal

            order.total = order_total
            order.save(update_fields=["total"])

        cart.clear()
        messages.success(request, f"Order #{order.pk} placed - pending producer confirmation.")
        return redirect("order_detail", pk=order.pk)

    return render(request, "orders/checkout.html", {
        "groups": cart.grouped_by_producer(),
        "total": cart.total,
    })


@login_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related("sub_orders__items", "sub_orders__producer"),
        pk=pk,
        customer=request.user,
    )
    return render(request, "orders/order_detail.html", {"order": order})


@login_required
def my_orders(request):
    orders = Order.objects.filter(customer=request.user).prefetch_related("sub_orders")
    return render(request, "orders/my_orders.html", {"orders": orders})
