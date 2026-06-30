from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Product

from .cart import Cart


def cart_view(request):
    cart = Cart(request)
    return render(request, "cart/cart.html", {
        "groups": cart.grouped_by_producer(),
    })


def _back_or(request, fallback_name):
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect(fallback_name)


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    quantity = int(request.POST.get("quantity", 1))
    cart.add(product_id, quantity)
    product = Product.objects.filter(pk=product_id).only("name").first()
    name = product.name if product else "προϊόν"
    messages.success(request, f"✓ Προστέθηκε στο καλάθι: {name}")
    return _back_or(request, "cart")


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    quantity = int(request.POST.get("quantity", 0))
    cart.set_quantity(product_id, quantity)
    if quantity == 0:
        messages.info(request, "Το προϊόν αφαιρέθηκε από το καλάθι.")
    else:
        messages.success(request, "Η ποσότητα ενημερώθηκε.")
    return redirect("cart")


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    messages.info(request, "Το προϊόν αφαιρέθηκε από το καλάθι.")
    return redirect("cart")
