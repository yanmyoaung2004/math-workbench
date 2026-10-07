"""OCR seam: honest stub, strict decoding, provider selection."""

import base64

import pytest

from workbench_math.ai.ocr import StubOCRProvider, decode_image, ocr_provider
from workbench_math.ai.provider import AIProviderError


def test_stub_refuses_honestly():
    with pytest.raises(AIProviderError, match="No OCR engine"):
        StubOCRProvider().extract_text(b"bytes")


def test_decode_guards():
    assert decode_image(base64.b64encode(b"abc").decode()) == b"abc"
    prefixed = "data:image/png;base64," + base64.b64encode(b"abc").decode()
    assert decode_image(prefixed) == b"abc"
    with pytest.raises(AIProviderError):
        decode_image("not base64!!!")
    with pytest.raises(AIProviderError):
        decode_image(base64.b64encode(b"x").decode() * 3_000_000)


def test_provider_selection():
    assert isinstance(ocr_provider("stub"), StubOCRProvider)
    with pytest.raises(AIProviderError):
        ocr_provider("tesseract")
