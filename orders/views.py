from collections import defaultdict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from cart.cart import Cart
from catalog.models import Product
from orders.exceptions import InsufficientStock
from orders.forms import CheckoutForm
from orders.models import Order, OrderItem, SubOrder


@login_required
def checkout(request: HttpRequest) -> HttpResponse:
    """Collect delivery details and turn the cart into an order."""
    cart = Cart(request)
    if not cart.data:
        return redirect('cart')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = _place_order(request.user, cart, form)
            except InsufficientStock:
                messages.error(request, 'Κάποιο προϊόν εξαντλήθηκε όσο ολοκληρώνατε την παραγγελία.')
                return redirect('cart')
            cart.clear()
            messages.success(request, f'Order #{order.pk} placed - pending producer confirmation.')
            return redirect('order-detail', pk=order.pk)
    else:
        form = CheckoutForm(initial={'full_name': request.user.get_full_name() or request.user.username})

    return render(request, 'orders/checkout.html', {
        'form': form,
        'groups': cart.grouped_by_producer(),
        'total': cart.total,
    })


def _place_order(customer: User, cart: Cart, form: CheckoutForm) -> Order:
    """Write the order, its sub-orders and its items, decrementing stock as it goes."""
    with transaction.atomic():
        order = form.save(commit=False)
        order.customer = customer
        order.save()

        grouped = defaultdict(list)
        for item in cart.items():
            grouped[item['product'].producer].append(item)

        order_total = Decimal('0.00')
        for producer, items in grouped.items():
            sub_order = SubOrder.objects.create(order=order, producer=producer)
            subtotal = Decimal('0.00')
            for item in items:
                product = item['product']
                _decrement_stock(product, item['quantity'])
                OrderItem.objects.create(
                    sub_order=sub_order,
                    product=product,
                    product_name=product.name,
                    unit=product.unit,
                    unit_price=product.price,
                    quantity=item['quantity'],
                )
                subtotal += product.price * item['quantity']
            sub_order.subtotal = subtotal
            sub_order.save(update_fields=['subtotal', 'updated_at'])
            order_total += subtotal

        order.total = order_total
        order.save(update_fields=['total', 'updated_at'])
    return order


def _decrement_stock(product: Product, quantity: int) -> None:
    """Take stock with a single conditional UPDATE, so two racing checkouts cannot oversell."""
    taken = Product.objects.filter(pk=product.pk, stock__gte=quantity).update(stock=F('stock') - quantity)
    if not taken:
        raise InsufficientStock(f'{product.name} has fewer than {quantity} left')


@login_required
def order_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """One of the signed-in customer's orders."""
    order = get_object_or_404(
        Order.objects.prefetch_related('sub_orders__items', 'sub_orders__producer'),
        pk=pk,
        customer=request.user,
    )
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def my_orders(request: HttpRequest) -> HttpResponse:
    """Every order the signed-in customer has placed."""
    orders = Order.objects.filter(customer=request.user).prefetch_related('sub_orders')
    return render(request, 'orders/my_orders.html', {'orders': orders})
