from fastapi.testclient import TestClient

import app

client = TestClient(app.app)


def test_create_and_fetch_task():
    response = client.post(
        "/api/tasks",
        json={"summary": "Review the local training data and verify the retrieval path.", "task_type": "document_retrieval"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    task_id = payload["id"]
    assert payload["workflow_state"] == "RECEIVED"

    fetch_response = client.get(f"/api/tasks/{task_id}")
    assert fetch_response.status_code == 200
    assert fetch_response.json()["summary"] == payload["summary"]


def test_task_execution_uses_approved_tool():
    create_response = client.post(
        "/api/tasks",
        json={"summary": "Search the local document library for an approved workflow reference.", "task_type": "document_retrieval"},
    )
    task_id = create_response.json()["id"]

    execute_response = client.post(
        f"/api/tasks/{task_id}/execute",
        json={
            "tool_name": "document_search",
            "arguments": {"query": "confidential workflow", "limit": 3},
            "query": "confidential workflow",
        },
    )
    assert execute_response.status_code == 200, execute_response.text
    payload = execute_response.json()
    assert payload["workflow_state"] == "COMPLETED"
    assert payload["tool_calls"]


def test_tools_list_is_approved_and_exposed():
    response = client.get("/api/tools")
    assert response.status_code == 200
    names = {tool["name"] for tool in response.json()["tools"]}
    assert {"document_search", "document_metadata_lookup", "calculate_basic_stats", "generate_report", "validate_file"}.issubset(names)


def test_invalid_tool_rejected():
    create_response = client.post(
        "/api/tasks",
        json={"summary": "Attempt to call a forbidden tool.", "task_type": "general_reasoning"},
    )
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/tasks/{task_id}/execute",
        json={"tool_name": "arbitrary_shell_command", "arguments": {"command": "echo hello"}},
    )
    assert response.status_code == 400


def test_model_routing_prefers_task_specific_local_model():
    from workflow_engine import select_model_for_task

    model_name, reason = select_model_for_task("document_retrieval")
    assert model_name in {"qwen2.5:3b", "llama3.2:latest"}
    assert "selected" in reason.lower() or "available" in reason.lower()

    task = client.post("/api/tasks", json={"summary": "Summarize a local document set", "task_type": "summarization"}).json()
    assert task["selected_model"] in {"qwen2.5:3b", "llama3.2:latest"}


def test_task_execution_tracks_history():
    create_response = client.post(
        "/api/tasks",
        json={"summary": "Track workflow execution history for an approved task.", "task_type": "analysis"},
    )
    task_id = create_response.json()["id"]
    execute_response = client.post(
        f"/api/tasks/{task_id}/execute",
        json={
            "tool_name": "calculate_basic_stats",
            "arguments": {"values": [1, 2, 3, 4]},
        },
    )
    assert execute_response.status_code == 200, execute_response.text
    task = client.get(f"/api/tasks/{task_id}").json()
    states = [event["state"] for event in task["execution_history"]]
    assert "VALIDATING" in states
    assert "COMPLETED" in states


def test_example_workflows_and_artifacts_are_exposed():
    examples_response = client.get("/api/workflows/examples")
    assert examples_response.status_code == 200, examples_response.text
    workflow_ids = {workflow["id"] for workflow in examples_response.json()["workflows"]}
    assert {"inspection-report-analysis", "local-csv-analysis", "engineering-drawing-analysis"}.issubset(workflow_ids)

    created_workflow = client.post("/api/workflows/examples/local-csv-analysis")
    assert created_workflow.status_code == 200, created_workflow.text
    task = created_workflow.json()
    assert task["workflow_state"] == "COMPLETED"
    assert task["artifacts"]

    artifact_payload = client.post(
        "/api/artifacts/generate",
        json={"title": "Manual Validation Note", "summary": "This note documents the output verification for the sample report.", "task_id": task["id"]},
    )
    assert artifact_payload.status_code == 200, artifact_payload.text
    artifact = artifact_payload.json()

    download_response = client.get(f"/api/artifacts/{artifact['id']}/download")
    assert download_response.status_code == 200, download_response.text
    assert "text/markdown" in download_response.headers.get("content-type", "")


def test_security_status_reports_local_only_configuration():
    security_response = client.get("/api/security/status")
    assert security_response.status_code == 200, security_response.text
    payload = security_response.json()
    assert payload["offline_mode"] is True
    assert payload["local_only"] is True
    assert payload["allowed_network"]

    status_response = client.get("/api/status")
    assert status_response.status_code == 200, status_response.text
    assert status_response.json()["offline_mode"] is True

    from ollama_client import OLLAMA_BASE_URL

    assert OLLAMA_BASE_URL.startswith("http://127.0.0.1")


def test_task_execution_header_auth_is_optional_until_enabled():
    create_response = client.post("/api/tasks", json={"summary": "Verify local-only execution policy", "task_type": "analysis"})
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/tasks/{task_id}/execute",
        json={"tool_name": "calculate_basic_stats", "arguments": {"values": [1, 2, 3]}},
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 200
