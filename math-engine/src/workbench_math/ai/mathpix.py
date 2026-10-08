"""Mathpix OCR provider (paid API, credentials at runtime).

API shape per Mathpix v3 docs (verify against a live key before release):
POST {base}/text with app_id/app_key headers and
{src: <data-url>, formats: ["latex_simplified", "text"]}.
Returns LaTeX, which maps directly onto our parser. Wire format is proven
against a local loopback server in tests; live accuracy needs a real key.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.request

from .ocr import OCRProvider
from .provider import AIProviderError


class MathpixOCRProvider(OCRProvider):
    name = "mathpix"

    def __init__(self, base_url: str = "", app_id: str = "", app_key: str = "",
                 timeout: float = 30.0):
        self.base_url = (base_url or os.environ.get(
            "WORKBENCH_MATHPIX_URL", "https://api.mathpix.com/v3")).rstrip("/")
        self.app_id = app_id or os.environ.get("WORKBENCH_MATHPIX_APP_ID", "")
        self.app_key = app_key or os.environ.get("WORKBENCH_MATHPIX_APP_KEY", "")
        self.timeout = timeout

    def extract_text(self, image_bytes: bytes) -> str:
        if not self.app_id or not self.app_key:
            raise AIProviderError(
                "Mathpix needs WORKBENCH_MATHPIX_APP_ID and WORKBENCH_MATHPIX_APP_KEY.")
        data_url = "data:image/png;base64," + base64.b64encode(image_bytes).decode()
        body = json.dumps({
            "src": data_url,
            "formats": ["latex_simplified", "text"],
            "data_options": {"include_latex": True},
        }).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + "/text", data=body,
            headers={"Content-Type": "application/json",
                     "app_id": self.app_id, "app_key": self.app_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderError(f"Mathpix request failed: {exc}") from exc
        text = (payload.get("latex_simplified") or payload.get("text") or "").strip()
        if not text:
            raise AIProviderError("Mathpix returned no readable text.")
        if text.startswith("\\(") and text.endswith("\\)"):
            text = text[2:-2]
        return text.strip()
