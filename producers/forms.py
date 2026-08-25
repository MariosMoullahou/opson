from django.forms import FileField, ModelForm

from catalog.models import Product
from core.forms import StyledFieldsMixin
from core.images import render_variants, validate_upload
from producers.models import Producer

PRODUCT_IMAGE_SIZES = {'card': 400, 'detail': 1000}
PRODUCER_COVER_SIZES = {'card': 600, 'detail': 1600}

_UPLOAD_HELP = 'JPEG, PNG ή WebP. Έως 8MB.'


class ProductForm(StyledFieldsMixin, ModelForm):
    """Create or edit one of the signed-in producer's products."""

    image = FileField(required=False, help_text=_UPLOAD_HELP)

    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'unit', 'unit_label', 'price', 'stock', 'emoji', 'is_active']

    def clean_image(self):
        return validate_upload(self.cleaned_data.get('image'))

    def save(self, commit: bool = True) -> Product:
        product = super().save(commit=False)
        upload = self.cleaned_data.get('image')
        if upload:
            variants = render_variants(upload, PRODUCT_IMAGE_SIZES)
            product.image_card = variants['card']
            product.image_detail = variants['detail']
        if commit:
            product.save()
        return product


class ProducerProfileForm(StyledFieldsMixin, ModelForm):
    """Edit the signed-in producer's own profile."""

    cover = FileField(required=False, help_text=_UPLOAD_HELP)

    class Meta:
        model = Producer
        fields = ['farm_name', 'village', 'region', 'bio', 'badge']

    def clean_cover(self):
        return validate_upload(self.cleaned_data.get('cover'))

    def save(self, commit: bool = True) -> Producer:
        producer = super().save(commit=False)
        upload = self.cleaned_data.get('cover')
        if upload:
            variants = render_variants(upload, PRODUCER_COVER_SIZES)
            producer.cover_card = variants['card']
            producer.cover_detail = variants['detail']
        if commit:
            producer.save()
        return producer
