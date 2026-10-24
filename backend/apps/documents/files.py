import base64
import io
import json
import subprocess
import sys
import warnings
from pathlib import Path

from PIL import Image, ImageChops, UnidentifiedImageError
from rest_framework.exceptions import ValidationError

MAX_SOURCE_BYTES = 4 * 1024**2
MAX_SIGNATURE_BYTES = 1024**2


def read_upload(upload, limit=MAX_SOURCE_BYTES):
    if upload is None:
        raise ValidationError({"file": ["Choose a file."]})
    if upload.size > limit:
        raise ValidationError({"file": [f"Use a file smaller than {limit // 1024**2} MB."]})
    raw = upload.read(limit + 1)
    if not raw or len(raw) > limit:
        raise ValidationError({"file": ["The file is empty or too large."]})
    return raw


def inspect_pdf(raw, *, page=1, render=True):
    if len(raw) > 8 * 1024**2 or not raw.startswith(b"%PDF-"):
        raise ValidationError({"file": ["Choose a valid PDF within the size limit."]})
    try:
        result = subprocess.run(
            [sys.executable, "-m", "apps.documents.pdf_worker"],
            input=json.dumps(
                {"pdf": base64.b64encode(raw).decode(), "page": page, "render": render}
            ).encode(),
            capture_output=True,
            timeout=10,
            check=True,
            cwd=Path(__file__).resolve().parents[2],
        )
        return json.loads(result.stdout)
    except (subprocess.SubprocessError, ValueError, OSError) as error:
        raise ValidationError(
            {"file": ["Could not read this PDF. Use an unencrypted PDF with at most 50 pages."]}
        ) from error


def clean_image(raw, *, signature=False):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as source:
                if source.format not in {"PNG", "JPEG", "WEBP"}:
                    raise ValueError("Unsupported image")
                if source.width * source.height > 8_000_000 or source.n_frames != 1:
                    raise ValueError("Image too large")
                image = source.convert("RGBA")
                image.thumbnail((1500, 1500))
                if signature:
                    if image.width < 12 or image.height < 8:
                        raise ValueError("Too small")
                    white = Image.new("RGBA", image.size, "white")
                    white.alpha_composite(image)
                    ink = ImageChops.difference(
                        white.convert("RGB"), Image.new("RGB", image.size, "white")
                    )
                    mask = ink.convert("L").point(lambda p: 255 if p > 40 else 0)
                    bounds = mask.getbbox()
                    if (
                        not bounds
                        or bounds[2] - bounds[0] < 8
                        or bounds[3] - bounds[1] < 5
                        or mask.histogram()[255] < 30
                    ):
                        raise ValueError("Blank signature")
                    left, top, right, bottom = bounds
                    image = image.crop(
                        (
                            max(0, left - 8),
                            max(0, top - 8),
                            min(image.width, right + 8),
                            min(image.height, bottom + 8),
                        )
                    )
                output = io.BytesIO()
                image.save(output, "PNG")
                return output.getvalue()
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as error:
        raise ValidationError(
            {
                "signature" if signature else "file": [
                    "Use a readable, non-blank PNG, JPEG or WebP image within the image limits."
                ]
            }
        ) from error


def source_preview(file, page=1):
    raw = read_upload(file)
    if raw.startswith(b"%PDF-"):
        return inspect_pdf(raw, page=page)
    if page != 1:
        raise ValidationError({"page": ["An image has one page."]})
    return {"pages": 1, "image": base64.b64encode(clean_image(raw)).decode()}
