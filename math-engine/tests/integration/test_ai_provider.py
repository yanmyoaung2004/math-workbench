"""Provider wire format proven against a local loopback HTTP server (no internet)."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from workbench_math.ai.openai_compat import OpenAICompatibleProvider
from workbench_math.ai.provider import AIProviderError


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        assert body["model"] == "test-model"
        assert body["messages"][0]["role"] == "system"
        payload = json.dumps(
            {"choices": [{"message": {"content": "loopback explanation"}}]}).encode()
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


def test_openai_compat_round_trip(server):
    provider = OpenAICompatibleProvider(base_url=server, api_key="k", model="test-model")
    assert provider.complete("Explain x = 6.") == "loopback explanation"


def test_missing_key_refuses_fast():
    provider = OpenAICompatibleProvider(base_url="http://127.0.0.1:1", api_key="")
    with pytest.raises(AIProviderError, match="No API key"):
        provider.complete("hi")


def test_unreachable_host_maps_to_provider_error(server):
    provider = OpenAICompatibleProvider(base_url="http://127.0.0.1:1", api_key="k")
    with pytest.raises(AIProviderError):
        provider.complete("hi")
