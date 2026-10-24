from fastapi.testclient import TestClient

import app

client = TestClient(app.app)


def test_document_upload_and_search_round_trip():
    content = "SovereignAI supports confidential workflow analysis and local retrieval for approvals."
    response = client.post(
        "/api/documents/upload",
        files={"file": ("sample.txt", content.encode("utf-8"), "text/plain")},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    document_id = payload["id"]
    assert payload["status"] == "indexed"
    assert payload["chunks"] >= 1

    documents_response = client.get("/api/documents")
    assert documents_response.status_code == 200
    files = documents_response.json()["documents"]
    assert any(item["id"] == document_id for item in files)

    search_response = client.post("/api/search", json={"query": "confidential workflow", "limit": 5})
    assert search_response.status_code == 200, search_response.text
    matches = search_response.json()["results"]
    assert matches
    assert any(match["document_id"] == document_id for match in matches)


def test_invalid_file_type_rejected():
    response = client.post(
        "/api/documents/upload",
        files={"file": ("bad.bin", b"not allowed", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_delete_document_removes_record():
    content = "Sensitive engineering document with maintenance data."
    response = client.post(
        "/api/documents/upload",
        files={"file": ("maintenance.txt", content.encode("utf-8"), "text/plain")},
    )
    document_id = response.json()["id"]

    delete_response = client.delete(f"/api/documents/{document_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "deleted"

    search_response = client.post("/api/search", json={"query": "maintenance", "limit": 5})
    assert search_response.status_code == 200
    assert all(match["document_id"] != document_id for match in search_response.json()["results"])
