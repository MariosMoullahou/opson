from django.contrib.auth.forms import UserCreationForm

from accounts.models import User
from core.forms import StyledFieldsMixin


class SignupForm(StyledFieldsMixin, UserCreationForm):
    """Registration for a customer account."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')
