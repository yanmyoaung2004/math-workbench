"""OCR seam for image input — abstraction first, engines plug in later.

Photomath proves the demand; this module keeps Math Workbench ready without
pretending OCR works offline today. Providers implement `extract_text`; the
default stub refuses honestly and points at typing. A real engine (on-device
Tesseract or cloud OCR behind the AI-provider pattern) slots in without
touching the protocol.
"""

from __future__ import annotations

import abc
import base64
import binascii

from .provider import AIProviderError


class OCRProvider(abc.ABC):
    name: str = "ocr"

    @abc.abstractmethod
    def extract_text(self, image_bytes: bytes) -> str:
        """Return recognized math text. Raises AIProviderError when unavailable."""
        raise NotImplementedError


class StubOCRProvider(OCRProvider):
    name = "stub-ocr"

    def extract_text(self, image_bytes: bytes) -> str:
        raise AIProviderError(
            "No OCR engine is configured. Type the problem instead, or connect "
            "an OCR engine (set WORKBENCH_OCR_PROVIDER).")


def decode_image(payload: str, limit_bytes: int = 2_000_000) -> bytes:
    """Decode a base64 image (optionally data-URL prefixed) with a size cap."""
    text = payload.strip()
    if "," in text and text.startswith("data:"):
        text = text.split(",", 1)[1]
    try:
        raw = base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AIProviderError("That image data is not valid base64.") from exc
    if len(raw) > limit_bytes:
        raise AIProviderError("That image is too large (limit 2 MB).")
    if not raw:
        raise AIProviderError("Empty image.")
    return raw


def ocr_provider(kind: str = "") -> OCRProvider:
    """Select OCR backend by WORKBENCH_OCR_PROVIDER (stub default)."""
    import os

    which = (kind or os.environ.get("WORKBENCH_OCR_PROVIDER", "stub")).strip().lower()
    if which != "stub":
        raise AIProviderError(f"Unknown OCR provider {which!r} (only 'stub' in V1).")
    return StubOCRProvider()  # real engines register here
