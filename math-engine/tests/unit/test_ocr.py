"""OCR seam: honest stub, strict decoding, provider selection."""

import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from workbench_math.ai.mathpix import MathpixOCRProvider
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
    assert isinstance(ocr_provider("mathpix"), MathpixOCRProvider)
    with pytest.raises(AIProviderError):
        ocr_provider("tesseract")


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        assert self.path == "/text"
        assert self.headers.get("app_id") == "id" and self.headers.get("app_key") == "key"
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        assert body["formats"] == ["latex_simplified", "text"]
        payload = json.dumps({"latex_simplified": "2x+5=17"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def server():
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def test_mathpix_wire_format(server):
    provider = MathpixOCRProvider(base_url=server, app_id="id", app_key="key")
    assert provider.extract_text(b"bytes") == "2x+5=17"


def test_mathpix_needs_credentials():
    provider = MathpixOCRProvider(base_url="http://127.0.0.1:1", app_id="", app_key="")
    with pytest.raises(AIProviderError, match="needs"):
        provider.extract_text(b"bytes")
