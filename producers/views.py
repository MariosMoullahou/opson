from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Category, Product
from orders.models import OrderStatus, SubOrder


def _producer_or_none(request):
    if not request.user.is_authenticated:
        return None
    return getattr(request.user, "producer_profile", None)


@login_required
def dashboard(request):
    producer = _producer_or_none(request)
    if producer is None:
        return HttpResponseForbidden("You are not registered as a producer.")
    sub_orders = (
        SubOrder.objects.filter(producer=producer)
        .select_related("order")
        .prefetch_related("items")
    )
    active = [s for s in sub_orders if s.status not in (OrderStatus.DELIVERED, OrderStatus.CANCELLED)]
    history = [s for s in sub_orders if s.status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED)]
    products = producer.products.all()
    return render(request, "producers/dashboard.html", {
        "producer": producer,
        "active_sub_orders": active,
        "history_sub_orders": history,
        "products": products,
    })


@login_required
@require_POST
def transition_suborder(request, pk):
    producer = _producer_or_none(request)
    if producer is None:
        return HttpResponseForbidden()
    sub = get_object_or_404(SubOrder, pk=pk, producer=producer)
    new_status = request.POST.get("status")
    try:
        sub.transition_to(new_status)
        messages.success(request, f"Order #{sub.order.pk} -> {sub.get_status_display()}")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("producer_dashboard")


@login_required
def product_create(request):
    producer = _producer_or_none(request)
    if producer is None:
        return HttpResponseForbidden()
    if request.method == "POST":
        Product.objects.create(
            producer=producer,
            name=request.POST.get("name"),
            description=request.POST.get("description", ""),
            unit=request.POST.get("unit", Product.Unit.PIECE),
            price=request.POST.get("price"),
            stock=int(request.POST.get("stock") or 0),
            image_url=request.POST.get("image_url", ""),
            category_id=request.POST.get("category") or None,
        )
        messages.success(request, "Product added.")
        return redirect("producer_dashboard")
    return render(request, "producers/product_form.html", {
        "categories": Category.objects.all(),
        "units": Product.Unit.choices,
    })
