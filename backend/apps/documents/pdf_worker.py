"""Isolated PDF parsing/rasterization. stdin bytes -> one bounded JSON response."""

import base64
import io
import json
import sys


def run():
    # PDFium is not thread safe. Run it in a short-lived child, never a web thread.
    if sys.platform != "win32":
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (384 * 1024**2, 384 * 1024**2))
        resource.setrlimit(resource.RLIMIT_CPU, (6, 6))
        resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024**2, 8 * 1024**2))
    import pypdfium2 as pdfium

    data = sys.stdin.buffer.read(12 * 1024**2 + 1)
    if len(data) > 12 * 1024**2:
        raise ValueError("Too large")
    payload = json.loads(data)
    raw = base64.b64decode(payload["pdf"], validate=True)
    if not raw.startswith(b"%PDF-"):
        raise ValueError("Not a PDF")
    with pdfium.PdfDocument(raw) as pdf:
        count = len(pdf)
        if not 1 <= count <= 50:
            raise ValueError("Too many pages")
        result = {"pages": count}
        if payload.get("render", True):
            index = payload.get("page", 1) - 1
            if not 0 <= index < count:
                raise ValueError("Invalid page")
            page = pdf[index]
            try:
                width, height = page.get_size()
                if not (1 <= width <= 20000 and 1 <= height <= 20000):
                    raise ValueError("Invalid dimensions")
                scale = min(1.8, 1500 / max(width, height))
                bitmap = page.render(scale=scale, rotation=0)
                try:
                    image = bitmap.to_pil().convert("RGB")
                    stream = io.BytesIO()
                    image.save(stream, format="PNG")
                    result["image"] = base64.b64encode(stream.getvalue()).decode()
                finally:
                    bitmap.close()
            finally:
                page.close()
        sys.stdout.write(json.dumps(result))


if __name__ == "__main__":
    try:
        run()
    except Exception:
        sys.exit(1)
