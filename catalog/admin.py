from django.contrib.admin import ModelAdmin, register

from catalog.models import Category, Product


@register(Category)
class CategoryAdmin(ModelAdmin):
    """Category nav entries."""

    list_display = ['name', 'slug', 'emoji', 'sort_order']
    search_fields = ['name']
    # Populated by Category.save(); the admin's prepopulate widget ASCII-slugifies and erases Greek.
    readonly_fields = ['slug', 'created_at', 'updated_at']


@register(Product)
class ProductAdmin(ModelAdmin):
    """Products offered by producers."""

    list_display = ['name', 'producer', 'category', 'price', 'unit', 'stock', 'is_active', 'agroverify_code']
    list_filter = ['category', 'is_active', 'unit']
    search_fields = ['name', 'producer__farm_name', 'agroverify_code']
    date_hierarchy = 'created_at'
    list_select_related = ['producer', 'category']
    readonly_fields = ['created_at', 'updated_at']
