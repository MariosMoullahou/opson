from collections import defaultdict
from decimal import Decimal

from catalog.models import Product

CART_SESSION_KEY = "cart"


class Cart:
    """Session-backed cart. Stores {product_id: quantity}."""

    def __init__(self, request):
        self.session = request.session
        self.data = self.session.setdefault(CART_SESSION_KEY, {})

    def _save(self):
        self.session[CART_SESSION_KEY] = self.data
        self.session.modified = True

    def add(self, product_id, quantity=1):
        pid = str(product_id)
        self.data[pid] = self.data.get(pid, 0) + int(quantity)
        self._save()

    def set_quantity(self, product_id, quantity):
        pid = str(product_id)
        if quantity <= 0:
            self.data.pop(pid, None)
        else:
            self.data[pid] = int(quantity)
        self._save()

    def remove(self, product_id):
        self.data.pop(str(product_id), None)
        self._save()

    def clear(self):
        self.data = {}
        self._save()

    def items(self):
        if not self.data:
            return []
        products = Product.objects.select_related("producer").filter(
            id__in=[int(pid) for pid in self.data.keys()]
        )
        result = []
        for p in products:
            qty = self.data.get(str(p.id), 0)
            result.append({
                "product": p,
                "quantity": qty,
                "line_total": p.price * qty,
            })
        return result

    def grouped_by_producer(self):
        groups = defaultdict(list)
        for item in self.items():
            groups[item["product"].producer].append(item)
        return groups

    @property
    def total(self):
        return sum((item["line_total"] for item in self.items()), Decimal("0.00"))

    @property
    def count(self):
        return sum(self.data.values())
