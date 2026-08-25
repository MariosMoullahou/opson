from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cart.cart import Cart
from cart.forms import CartAddForm, CartUpdateForm
from catalog.models import Product


def cart_view(request: HttpRequest) -> HttpResponse:
    """The cart, grouped by producer."""
    cart = Cart(request)
    return render(request, 'cart/cart.html', {'groups': cart.grouped_by_producer()})


@require_POST
def cart_add(request: HttpRequest, product_id: int) -> HttpResponse:
    """Add a validated quantity of one product to the cart."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    form = CartAddForm(request.POST, product=product)
    if not form.is_valid():
        messages.error(request, form.errors['quantity'][0])
        return redirect('product-detail', pk=product.pk)

    Cart(request).add(product.pk, form.cleaned_data['quantity'])
    messages.success(request, f'✓ Προστέθηκε στο καλάθι: {product.name}')
    return redirect('cart')


@require_POST
def cart_update(request: HttpRequest, product_id: int) -> HttpResponse:
    """Set the quantity on one cart line; zero removes it."""
    product = get_object_or_404(Product, pk=product_id)
    form = CartUpdateForm(request.POST, product=product)
    if not form.is_valid():
        messages.error(request, form.errors['quantity'][0])
        return redirect('cart')

    quantity = form.cleaned_data['quantity']
    Cart(request).set_quantity(product.pk, quantity)
    if quantity == 0:
        messages.info(request, 'Το προϊόν αφαιρέθηκε από το καλάθι.')
    else:
        messages.success(request, 'Η ποσότητα ενημερώθηκε.')
    return redirect('cart')


@require_POST
def cart_remove(request: HttpRequest, product_id: int) -> HttpResponse:
    """Drop one product from the cart."""
    Cart(request).remove(product_id)
    messages.info(request, 'Το προϊόν αφαιρέθηκε από το καλάθι.')
    return redirect('cart')
