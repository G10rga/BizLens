"""CLI worker: run OCR in a separate process so OOM/crashes don't kill Flask."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: receipt_ocr_worker.py <image_path>"}))
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(json.dumps({"error": f"missing file: {path}"}))
        return 2

    # Import inside worker so parent gunicorn stays light until needed
    from app.services.receipt_ocr import parse_image

    raw = path.read_bytes()
    parsed = parse_image(raw, filename=path.name)
    print(json.dumps(parsed, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
