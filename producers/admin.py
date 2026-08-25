from django.contrib.admin import ModelAdmin, register

from producers.models import Producer


@register(Producer)
class ProducerAdmin(ModelAdmin):
    """Farms and workshops selling on the marketplace."""

    list_display = ['farm_name', 'user', 'village', 'region', 'badge', 'agroverify_id', 'created_at']
    list_filter = ['badge', 'region']
    search_fields = ['farm_name', 'village', 'agroverify_id', 'user__username']
    date_hierarchy = 'created_at'
    list_select_related = ['user']
    # Populated by Producer.save(); the admin's prepopulate widget ASCII-slugifies and erases Greek.
    readonly_fields = ['slug', 'created_at', 'updated_at']
