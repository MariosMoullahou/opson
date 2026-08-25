from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_FORMATS = frozenset({'JPEG', 'PNG', 'WEBP'})
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_DIMENSION = 6000
WEBP_QUALITY = 82
WEBP_METHOD = 6

# thumbnail() needs a height bound too; four times the width lets any realistic photo stay width-bound.
_MAX_ASPECT_RATIO = 4


def validate_upload(upload: UploadedFile | None) -> UploadedFile | None:
    """Reject anything that is not a reasonable photo, with a message a producer can act on."""
    if upload is None:
        return None
    if upload.size > MAX_UPLOAD_BYTES:
        raise ValidationError('Η εικόνα είναι πολύ μεγάλη (μέγιστο 8MB).')

    try:
        image = Image.open(upload)
        image.verify()  # verify() consumes the file object, so every check below reopens it
        upload.seek(0)
        image = Image.open(upload)
    except (UnidentifiedImageError, OSError) as exc:
        # Pillow's own error is English and mentions file objects; a producer needs to know to re-export.
        raise ValidationError('Το αρχείο δεν είναι έγκυρη εικόνα.') from exc

    if image.format not in ALLOWED_FORMATS:
        raise ValidationError('Δεκτές μορφές: JPEG, PNG, WebP.')
    if max(image.size) > MAX_DIMENSION:
        raise ValidationError('Η εικόνα έχει πολύ μεγάλες διαστάσεις.')

    upload.seek(0)
    return upload


def render_variants(upload: UploadedFile, sizes: dict[str, int]) -> dict[str, ContentFile]:
    """Resize one upload into named WebP renditions, stripping EXIF."""
    upload.seek(0)
    source = Image.open(upload)
    source = ImageOps.exif_transpose(source)  # phones store a rotation flag rather than rotated pixels
    if source.mode != 'RGB':
        source = source.convert('RGB')

    variants = {}
    for name, width in sizes.items():
        variant = source.copy()
        variant.thumbnail((width, width * _MAX_ASPECT_RATIO), Image.LANCZOS)
        buffer = BytesIO()
        # Re-encoding into a fresh buffer is what drops EXIF, and with it the producer's home GPS.
        variant.save(buffer, format='WEBP', quality=WEBP_QUALITY, method=WEBP_METHOD)
        # A name matters: FileField hands it to upload_to, and an unnamed ContentFile passes None.
        variants[name] = ContentFile(buffer.getvalue(), name=f'{name}.webp')
    return variants
