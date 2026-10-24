from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict

OLLAMA_BASE_URL = "http://127.0.0.1:11434"


@dataclass
class OllamaModel:
    name: str
    model: str | None = None
    size: int | None = None
    modified_at: str | None = None
    digest: str | None = None
    capabilities: list[str] | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _request_json(path: str, payload: dict | None = None, method: str = "GET") -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{OLLAMA_BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:  # pragma: no cover - actual runtime guard
        raise RuntimeError(f"Unable to reach the local Ollama service at {OLLAMA_BASE_URL}") from exc


def availability() -> tuple[bool, str | None, list[str]]:
    try:
        tags = _request_json("/api/tags")
    except RuntimeError:
        return False, None, []

    models = tags.get("models", [])
    names = []
    for item in models:
        name = item.get("name") or item.get("model")
        if name:
            names.append(name)

    version = None
    try:
        version_response = _request_json("/api/version")
        version = version_response.get("version")
    except RuntimeError:
        version = None

    return bool(names), version, names


def list_models() -> list[OllamaModel]:
    tags = _request_json("/api/tags")
    models: list[OllamaModel] = []
    for item in tags.get("models", []):
        models.append(
            OllamaModel(
                name=item.get("name") or item.get("model") or "unknown",
                model=item.get("model"),
                size=item.get("size"),
                modified_at=item.get("modified_at"),
                digest=item.get("digest"),
                capabilities=item.get("capabilities"),
            )
        )
    return models


def generate_text(model: str, prompt: str, system: str | None = None, temperature: float = 0.2, max_tokens: int = 256) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "system": system,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    response = _request_json("/api/generate", payload=payload, method="POST")
    return response.get("response", "")


def chat_completion(model: str, messages: list[dict], temperature: float = 0.2, max_tokens: int = 256) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    response = _request_json("/api/chat", payload=payload, method="POST")
    message = response.get("message", {})
    return message.get("content", "")
