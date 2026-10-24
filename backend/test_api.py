from unittest.mock import patch

from fastapi.testclient import TestClient

import app

client = TestClient(app.app)


def test_health_status():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_system_status_endpoint():
    with patch("app.availability", return_value=(True, "0.1.0", ["qwen2.5:3b"])):
        response = client.get("/api/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ready", "partial"}
    assert payload["environment"] == "local"
    assert payload["models"] == ["qwen2.5:3b"]
    assert isinstance(payload["warnings"], list)


def test_models_endpoint():
    with patch("app.list_models", return_value=[type("Model", (), {"name": "qwen2.5:3b"})()]):
        response = client.get("/api/models")
    assert response.status_code == 200
    payload = response.json()
    assert payload["models"] == ["qwen2.5:3b"]
    assert payload["warnings"] == []


def test_ollama_generate_endpoint():
    with patch("app.generate_text", return_value="Local model is working."):
        response = client.post(
            "/api/ollama/generate",
            json={"model": "qwen2.5:3b", "prompt": "Confirm viability."},
        )
    assert response.status_code == 200
    assert response.json()["response"] == "Local model is working."


def test_ollama_chat_endpoint():
    with patch("app.chat_completion", return_value="Reply from local model."):
        response = client.post(
            "/api/ollama/chat",
            json={"model": "qwen2.5:3b", "messages": [{"role": "user", "content": "Hi"}]},
        )
    assert response.status_code == 200
    assert response.json()["response"] == "Reply from local model."
