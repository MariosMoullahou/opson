from django.forms import ModelForm

from core.forms import StyledFieldsMixin
from orders.models import Order


class CheckoutForm(StyledFieldsMixin, ModelForm):
    """Delivery details for an order."""

    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'address', 'notes']
