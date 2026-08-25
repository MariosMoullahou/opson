import pytest
from django.core.exceptions import ValidationError
from PIL import Image

from core.images import MAX_UPLOAD_BYTES, render_variants, validate_upload
from core.tests.factories import GPS_IFD_TAG, ROTATE_90_CW, a_text_file, an_image_file

CARD_WIDTH = 400
DETAIL_WIDTH = 1000
SIZES = {'card': CARD_WIDTH, 'detail': DETAIL_WIDTH}


def _opened(variant) -> Image.Image:
    variant.seek(0)
    return Image.open(variant)


class TestRenderVariants:
    def test_every_requested_rendition_is_produced(self):
        """A single upload has to fill both image fields; a missing key would save an empty field silently."""
        variants = render_variants(an_image_file(), SIZES)

        assert set(variants) == {'card', 'detail'}

    def test_renditions_are_bound_by_their_named_width(self):
        """The card rendition exists to keep listing pages small; shipping detail-sized bytes defeats it."""
        variants = render_variants(an_image_file(size=(2400, 1600)), SIZES)

        assert _opened(variants['card']).width == CARD_WIDTH
        assert _opened(variants['detail']).width == DETAIL_WIDTH

    def test_aspect_ratio_survives_resizing(self):
        """Squashed produce photos look like a broken site, so resizing must never distort."""
        variants = render_variants(an_image_file(size=(2000, 1000)), SIZES)

        card = _opened(variants['card'])
        assert card.height == pytest.approx(card.width / 2, abs=1)

    def test_an_image_smaller_than_the_target_is_not_upscaled(self):
        """Blowing up a small upload adds bytes and blur without adding detail."""
        variants = render_variants(an_image_file(size=(200, 150)), SIZES)

        assert _opened(variants['detail']).width == 200

    def test_output_is_webp(self):
        """The whole media pipeline assumes .webp keys in the bucket."""
        variants = render_variants(an_image_file(), SIZES)

        assert _opened(variants['card']).format == 'WEBP'

    def test_each_variant_is_named(self):
        """FileField passes ContentFile.name straight to upload_to; an unnamed file passes None."""
        variants = render_variants(an_image_file(), SIZES)

        assert variants['card'].name == 'card.webp'

    def test_a_rotated_phone_photo_comes_out_upright(self):
        """Phone photos carry orientation in EXIF; ignoring it renders every farm photo sideways."""
        upload = an_image_file(size=(1200, 800), orientation=ROTATE_90_CW)

        card = _opened(render_variants(upload, {'card': CARD_WIDTH})['card'])

        assert card.height > card.width

    def test_output_carries_no_exif(self):
        """Re-encoding is what strips metadata; without it a producer's home GPS ships with their honey photo."""
        upload = an_image_file(orientation=ROTATE_90_CW, with_gps=True)

        exif = _opened(render_variants(upload, {'card': CARD_WIDTH})['card']).getexif()

        assert GPS_IFD_TAG not in exif
        assert not dict(exif)

    def test_a_transparent_png_is_flattened_rather_than_crashing(self):
        """WebP encoding of a palette or alpha image fails unless it is converted first."""
        upload = an_image_file(name='logo.png', image_format='PNG', mode='RGBA')

        variants = render_variants(upload, {'card': CARD_WIDTH})

        assert _opened(variants['card']).width == CARD_WIDTH


class TestValidateUpload:
    def test_a_blank_field_is_allowed_through(self):
        """Both image fields are optional; an untouched form must not raise."""
        assert validate_upload(None) is None

    def test_a_valid_photo_is_returned_rewound(self):
        """The caller reads the file straight after validating, so the cursor has to be back at zero."""
        upload = an_image_file()

        validated = validate_upload(upload)

        assert validated is upload
        assert upload.tell() == 0

    def test_an_oversized_upload_is_rejected(self):
        """An 8MB cap is what keeps a producer's 40MB DSLR export from tying up the request."""
        upload = an_image_file()
        upload.size = MAX_UPLOAD_BYTES + 1

        with pytest.raises(ValidationError):
            validate_upload(upload)

    def test_a_non_image_is_rejected(self):
        """A renamed .txt reaching Pillow in the model layer would raise something a producer cannot read."""
        with pytest.raises(ValidationError):
            validate_upload(a_text_file())

    def test_an_absurdly_large_canvas_is_rejected(self):
        """A small file can still decode to a huge bitmap and exhaust memory during resizing."""
        upload = an_image_file(size=(7000, 100))

        with pytest.raises(ValidationError):
            validate_upload(upload)
