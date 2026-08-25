class OrderError(Exception):
    """Base class for order failures the checkout view is expected to handle."""


class InsufficientStock(OrderError):
    """Raised when stock ran out between cart validation and the checkout write."""
