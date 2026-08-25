from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Product
from orders.enums import OrderStatus
from orders.models import SubOrder
from producers.forms import ProducerProfileForm, ProductForm
from producers.models import Producer

_CLOSED_STATUSES = [OrderStatus.DELIVERED, OrderStatus.CANCELLED]


def _producer_or_404(request: HttpRequest) -> Producer:
    """Every view here is producer-scoped; a customer reaching one is a 404, not a hint."""
    producer = getattr(request.user, 'producer_profile', None)
    if producer is None:
        raise Http404('Not registered as a producer.')
    return producer


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """The producer's orders and products."""
    producer = _producer_or_404(request)
    sub_orders = SubOrder.objects.filter(producer=producer).select_related('order').prefetch_related('items')
    return render(request, 'producers/dashboard.html', {
        'producer': producer,
        'active_sub_orders': sub_orders.exclude(status__in=_CLOSED_STATUSES),
        'history_sub_orders': sub_orders.filter(status__in=_CLOSED_STATUSES),
        'products': producer.products.all(),
    })


@login_required
@require_POST
def transition_suborder(request: HttpRequest, pk: int) -> HttpResponse:
    """Move one of the producer's sub-orders along its fulfilment pipeline."""
    producer = _producer_or_404(request)
    sub_order = get_object_or_404(SubOrder, pk=pk, producer=producer)
    try:
        sub_order.transition_to(request.POST.get('status'))
        messages.success(request, f'Order #{sub_order.order.pk} -> {sub_order.get_status_display()}')
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect('producer-dashboard')


@login_required
def product_create(request: HttpRequest) -> HttpResponse:
    """Add a product to the signed-in producer's catalog."""
    producer = _producer_or_404(request)
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save(commit=False)
        product.producer = producer  # never a form field: it would let a producer post another's id
        product.save()
        messages.success(request, 'Το προϊόν προστέθηκε.')
        return redirect('producer-dashboard')
    return render(request, 'producers/product_form.html', {'form': form, 'product': None})


@login_required
def product_update(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit one of the signed-in producer's own products."""
    producer = _producer_or_404(request)
    product = get_object_or_404(Product, pk=pk, producer=producer)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Το προϊόν ενημερώθηκε.')
        return redirect('producer-dashboard')
    return render(request, 'producers/product_form.html', {'form': form, 'product': product})


@login_required
def profile_update(request: HttpRequest) -> HttpResponse:
    """Edit the signed-in producer's own profile."""
    producer = _producer_or_404(request)
    form = ProducerProfileForm(request.POST or None, request.FILES or None, instance=producer)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Το προφίλ ενημερώθηκε.')
        return redirect('producer-dashboard')
    return render(request, 'producers/profile_form.html', {'form': form, 'producer': producer})
