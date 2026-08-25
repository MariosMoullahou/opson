from django.utils.text import slugify


def greek_slug(value: str) -> str:
    """Slugify preserving Greek characters; ASCII slugify erases Greek input entirely."""
    return slugify(value, allow_unicode=True)
