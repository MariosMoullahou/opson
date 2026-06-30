from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "producer", "category", "price", "unit", "stock", "is_active", "agroverify_code")
    list_filter = ("category", "is_active", "producer")
    search_fields = ("name", "producer__farm_name", "agroverify_code")
