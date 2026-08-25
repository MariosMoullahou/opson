from orders.models import Order, OrderItem, SubOrder
from producers.models import Producer
from producers.tests.factories import a_producer, a_user


def an_order(*, customer=None, **fields) -> Order:
    """A saved order with delivery details filled in."""
    customer = customer or a_user(username=f'customer-{Order.objects.count()}')
    fields.setdefault('full_name', 'Μαρία Κ.')
    fields.setdefault('phone', '+30 210 1234567')
    fields.setdefault('address', 'Ερμού 1, Αθήνα')
    return Order.objects.create(customer=customer, **fields)


def a_sub_order(*, order: Order | None = None, producer: Producer | None = None, **fields) -> SubOrder:
    """A saved sub-order under its own order and producer."""
    return SubOrder.objects.create(order=order or an_order(), producer=producer or a_producer(), **fields)


def an_order_item(*, sub_order: SubOrder | None = None, product=None, **fields) -> OrderItem:
    """A saved line item, with the product snapshot filled from the product."""
    from catalog.tests.factories import a_product  # local: avoids a factory import cycle

    product = product or a_product()
    sub_order = sub_order or a_sub_order(producer=product.producer)
    fields.setdefault('product_name', product.name)
    fields.setdefault('unit', product.unit)
    fields.setdefault('unit_price', product.price)
    fields.setdefault('quantity', 1)
    return OrderItem.objects.create(sub_order=sub_order, product=product, **fields)
