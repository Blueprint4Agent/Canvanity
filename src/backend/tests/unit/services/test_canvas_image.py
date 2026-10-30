from io import BytesIO

import pytest
from PIL import Image

from app.core.error.asset_exception import AssetErrorCode, AssetException
from app.services.asset import normalize_canvas_image


def encoded_image(format="PNG", *, animation=False):
    output = BytesIO()
    image = Image.new("RGBA" if format != "JPEG" else "RGB", (12, 8), (200, 10, 20))
    exif = Image.Exif()
    exif[270] = "private description"
    exif[274] = 6
    options = {"exif": exif} if format != "GIF" else {}
    if animation:
        options.update(
            save_all=True,
            append_images=[Image.new("RGBA", (12, 8), "blue")],
            duration=[80, 120],
            loop=2,
        )
    image.save(output, format, **options)
    return output.getvalue()


@pytest.mark.parametrize("format", ["PNG", "JPEG", "WEBP", "GIF"])
def test_real_formats_normalize_and_remove_private_metadata(format):
    normalized = normalize_canvas_image(encoded_image(format))
    with Image.open(BytesIO(normalized.data)) as image:
        assert image.format == "WEBP" and not image.getexif()
        assert "icc_profile" not in image.info and "xmp" not in image.info
        assert image.size == ((12, 8) if format == "GIF" else (8, 12))
        assert normalized.frames == 1


def test_transparency_and_bounded_animation_are_preserved():
    output = BytesIO()
    Image.new("RGBA", (6, 4), (100, 80, 20, 128)).save(output, "PNG")
    with Image.open(BytesIO(normalize_canvas_image(output.getvalue()).data)) as image:
        assert image.getpixel((0, 0))[3] == 128
    normalized = normalize_canvas_image(encoded_image("GIF", animation=True))
    with Image.open(BytesIO(normalized.data)) as image:
        assert image.n_frames == normalized.frames == 2 and image.info["loop"] == 2
        image.seek(1)
        assert image.convert("RGB").getpixel((1, 1))[2] > 200


@pytest.mark.parametrize(
    "data", [b"", b"not image", b'<svg xmlns="http://www.w3.org/2000/svg"/>', b"GIF89a\x01\x00"]
)
def test_spoofed_and_truncated_images_are_rejected(data):
    with pytest.raises(AssetException) as caught:
        normalize_canvas_image(data)
    assert caught.value.code == AssetErrorCode.INVALID_IMAGE.code


@pytest.mark.parametrize(
    "bound,value,animation", [("MAX_IMAGE_PIXELS", 10, False), ("MAX_IMAGE_FRAMES", 1, True)]
)
def test_decoded_dimensions_and_frame_limits_are_enforced(monkeypatch, bound, value, animation):
    monkeypatch.setattr("app.services.asset." + bound, value)
    with pytest.raises(AssetException) as caught:
        normalize_canvas_image(encoded_image("GIF", animation=animation))
    assert caught.value.code == AssetErrorCode.INVALID_IMAGE.code


def test_normalized_output_also_has_a_byte_limit(monkeypatch):
    monkeypatch.setattr("app.services.asset.MAX_IMAGE_BYTES", 1)
    with pytest.raises(AssetException) as caught:
        normalize_canvas_image(encoded_image())
    assert caught.value.code == AssetErrorCode.TOO_LARGE.code
