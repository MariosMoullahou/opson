from django.contrib import admin

from .models import Producer


@admin.register(Producer)
class ProducerAdmin(admin.ModelAdmin):
    list_display = ("farm_name", "user", "village", "agroverify_id", "created_at")
    search_fields = ("farm_name", "village", "agroverify_id")
    prepopulated_fields = {"slug": ("farm_name",)}
