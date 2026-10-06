"""OpenAI-compatible REST provider (stdlib urllib — no SDK dependency).

Works against OpenAI, OpenRouter, Gemini-openai-endpoint, or any local server
speaking /chat/completions. Key and endpoint come from the environment at call
time; tests prove the wire format against a local stub HTTP server.
"""

from __future__ import annotations

import json
import os
import urllib.request

from .provider import AIProviderError, ProviderPort


class OpenAICompatibleProvider(ProviderPort):
    name = "openai_compat"

    def __init__(self, base_url: str = "", api_key: str = "", model: str = "",
                 timeout: float = 20.0):
        self.base_url = (base_url or os.environ.get("WORKBENCH_AI_BASE_URL",
                                                     "https://api.openai.com/v1")).rstrip("/")
        self.api_key = api_key or os.environ.get("WORKBENCH_AI_KEY", "")
        self.model = model or os.environ.get("WORKBENCH_AI_MODEL", "gpt-4o-mini")
        self.timeout = timeout

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 500) -> str:
        if not self.api_key:
            raise AIProviderError("No API key (set WORKBENCH_AI_KEY).")
        body = json.dumps({
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system or "You are a GCSE maths tutor."},
                {"role": "user", "content": prompt},
            ],
        }).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + "/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return payload["choices"][0]["message"]["content"]
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderError(f"AI request failed: {exc}") from exc
