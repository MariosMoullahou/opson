from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

ORIENTATION_TAG = 0x0112
GPS_IFD_TAG = 0x8825
GPS_LATITUDE_REF_TAG = 1
GPS_LATITUDE_TAG = 2

ROTATE_90_CW = 6


def an_image_file(
    *,
    name: str = 'photo.jpg',
    size: tuple[int, int] = (1200, 800),
    image_format: str = 'JPEG',
    mode: str = 'RGB',
    orientation: int | None = None,
    with_gps: bool = False,
) -> SimpleUploadedFile:
    """An in-memory upload, optionally carrying the EXIF a phone camera would attach."""
    color = (120, 160, 90, 128) if mode == 'RGBA' else (120, 160, 90)
    image = Image.new(mode, size, color=color)
    buffer = BytesIO()
    save_kwargs = {}

    if orientation is not None or with_gps:
        exif = Image.Exif()
        if orientation is not None:
            exif[ORIENTATION_TAG] = orientation
        if with_gps:
            gps = exif.get_ifd(GPS_IFD_TAG)
            gps[GPS_LATITUDE_REF_TAG] = 'N'
            gps[GPS_LATITUDE_TAG] = ((37, 1), (58, 1), (0, 1))
        save_kwargs['exif'] = exif.tobytes()

    image.save(buffer, format=image_format, **save_kwargs)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f'image/{image_format.lower()}')


def a_text_file(name: str = 'notes.txt') -> SimpleUploadedFile:
    """A file that is emphatically not an image."""
    return SimpleUploadedFile(name, b'this is not a photo', content_type='text/plain')
