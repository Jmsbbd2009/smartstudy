"""Untrusted PDF parser entry point. Invoked only in a resource-limited subprocess."""

import json
import sys
import os
import logging
import subprocess
import tempfile
from pathlib import Path


def limits():
    import resource

    resource.setrlimit(resource.RLIMIT_AS, (768 * 1024 * 1024, 768 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (18, 18))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024 * 1024, 32 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))


def main():
    limits()
    logging.disable(logging.CRITICAL)
    from pypdf import PdfReader

    path = Path(sys.argv[1])
    mode = sys.argv[2]
    reader = PdfReader(path, strict=True)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are unsupported")
    count = len(reader.pages)
    if not 1 <= count <= 300:
        raise ValueError("Page limit")
    pages = []
    if mode == "extract":
        total = 0
        for i, page in enumerate(reader.pages):
            text = (page.extract_text() or "").replace("\x00", "").strip()
            truncated = len(text) > 12000
            text = text[:12000]
            total += len(text)
            if total > 1500000:
                raise ValueError("Text limit")
            pages.append(
                {"page_number": i + 1, "text": text, "method": "TEXT_TRUNCATED" if truncated else "TEXT"}
            )
    else:
        start, end = int(sys.argv[3]), int(sys.argv[4])
        if not 1 <= start <= end <= count or end - start > 2:
            raise ValueError("OCR range")
        language = os.getenv("OCR_LANG", "eng")
        # No shell interpolation, network URLs, PDF scripting or external links are executed.
        with tempfile.TemporaryDirectory(prefix="study-ocr-") as tmp:
            for number in range(start, end + 1):
                base = Path(tmp) / "page"
                subprocess.run(
                    [
                        "pdftoppm",
                        "-f",
                        str(number),
                        "-l",
                        str(number),
                        "-singlefile",
                        "-scale-to",
                        "1600",
                        "-png",
                        str(path),
                        str(base),
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=12,
                )
                result = subprocess.run(
                    ["tesseract", str(base) + ".png", "stdout", "-l", language, "--psm", "6"],
                    capture_output=True,
                    check=True,
                    timeout=15,
                    env={**os.environ, "OMP_THREAD_LIMIT": "1"},
                )
                pages.append(
                    {
                        "page_number": number,
                        "text": result.stdout.decode("utf-8", errors="replace")
                        .replace("\x00", "")
                        .strip()[:12000],
                        "method": "OCR_UNVERIFIED",
                    }
                )
    print(json.dumps({"page_count": count, "pages": pages}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(2)
