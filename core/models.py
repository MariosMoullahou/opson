from django.db.models import DateTimeField, Model


class CreateUpdateDateModel(Model):
    """Timestamps every concrete model in the project inherits."""

    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        abstract = True
