from django.core.exceptions import ValidationError
from django.forms import Form, IntegerField

from catalog.models import Product

MAX_QUANTITY_PER_LINE = 99


class CartAddForm(Form):
    """Quantity to add to the cart, bounded by what the product actually has."""

    quantity = IntegerField(min_value=1, max_value=MAX_QUANTITY_PER_LINE)

    def __init__(self, *args, product: Product, **kwargs) -> None:
        self.product = product
        super().__init__(*args, **kwargs)

    def clean_quantity(self) -> int:
        quantity = self.cleaned_data['quantity']
        if quantity > self.product.stock:
            raise ValidationError('Δεν υπάρχει αρκετό απόθεμα.')
        return quantity


class CartUpdateForm(CartAddForm):
    """Quantity to set on an existing cart line; zero removes it."""

    quantity = IntegerField(min_value=0, max_value=MAX_QUANTITY_PER_LINE)
