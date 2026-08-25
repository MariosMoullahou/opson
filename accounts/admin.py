from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin

from accounts.models import User


@register(User)
class CustomUserAdmin(UserAdmin):
    """Marketplace accounts. Producer status is the producer_profile relation, not a field."""

    list_display = ['username', 'email', 'phone', 'is_staff']
    list_filter = ['is_staff', 'is_active']
    search_fields = ['username', 'email', 'phone']
    fieldsets = UserAdmin.fieldsets + (
        ('Opson', {'fields': ('phone',)}),
    )
