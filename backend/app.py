from __future__ import annotations

import os
import subprocess
from typing import Any

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from document_store import delete_document, list_documents, search_documents, upload_document
from ollama_client import availability, chat_completion, generate_text, list_models
from workflow_engine import (
    ARTIFACT_DIR,
    EXAMPLE_WORKFLOWS,
    TOOL_REGISTRY,
    create_example_workflow,
    create_task,
    execute_task,
    fetch_artifact,
    fetch_task,
    generate_report_artifact,
    list_artifacts,
    list_tasks,
)


class GenerateRequest(BaseModel):
    model: str
    prompt: str
    system: str | None = None
    temperature: float = 0.2
    max_tokens: int = 256


class ChatRequest(BaseModel):
    model: str
    messages: list[dict[str, str]]
    temperature: float = 0.2
    max_tokens: int = 256


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


class TaskCreateRequest(BaseModel):
    summary: str
    task_type: str = "general_reasoning"
    preferred_model: str | None = None
    query: str | None = None


class TaskExecuteRequest(BaseModel):
    tool_name: str | None = None
    arguments: dict[str, Any] = {}
    query: str | None = None


class SystemStatus(BaseModel):
    status: str
    environment: str
    python_version: str
    node_version: str | None
    offline_mode: bool
    ollama_available: bool
    ollama_version: str | None
    models: list[str]
    warnings: list[str]


def _run_command(command: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 127, "", "command not found"


OFFLINE_MODE = os.getenv("SOVEREIGNAI_OFFLINE_MODE", "true").lower() not in {"false", "0", "no"}
REQUIRE_TOOL_AUTH = os.getenv("SOVEREIGNAI_REQUIRE_TOOL_AUTH", "false").lower() in {"1", "true", "yes"}
EXPECTED_API_TOKEN = os.getenv("SOVEREIGNAI_API_TOKEN")

app = FastAPI(title="SovereignAI Backend", version="0.1.0")


def _validate_authorization_header(authorization: str | None, tool_name: str | None = None) -> None:
    if not REQUIRE_TOOL_AUTH:
        return
    if not EXPECTED_API_TOKEN:
        raise HTTPException(status_code=500, detail="Tool authorization is enabled but no local API token is configured.")
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header is required for tool execution.")
    token = authorization.replace("Bearer ", "", 1).strip()
    if token != EXPECTED_API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid local API token for tool execution.")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "sovereignai-backend"}


@app.get("/api/status", response_model=SystemStatus)
def get_status() -> SystemStatus:
    python_version = f"Python {os.sys.version.split()[0]}"
    node_version = None
    node_code, node_stdout, _ = _run_command(["node", "--version"])
    if node_code == 0:
        node_version = node_stdout.strip()

    try:
        ollama_available, ollama_version, model_names = availability()
        warnings: list[str] = []
        if not ollama_available:
            warnings.append("Ollama is not reachable on http://127.0.0.1:11434")
        models = model_names
    except RuntimeError as exc:
        ollama_available = False
        ollama_version = None
        models = []
        warnings = [str(exc)]

    return SystemStatus(
        status="ready" if ollama_available or not warnings else "partial",
        environment="local",
        python_version=python_version,
        node_version=node_version,
        offline_mode=OFFLINE_MODE,
        ollama_available=ollama_available,
        ollama_version=ollama_version,
        models=models,
        warnings=warnings,
    )


@app.get("/api/security/status")
def get_security_status() -> dict[str, Any]:
    return {
        "offline_mode": OFFLINE_MODE,
        "tool_auth_required": REQUIRE_TOOL_AUTH,
        "local_only": True,
        "allowed_network": ["127.0.0.1", "localhost"],
        "allowed_extensions": [".txt", ".md", ".csv", ".json", ".html", ".htm", ".pdf", ".docx", ".xlsx", ".pptx", ".png", ".jpg", ".jpeg"],
        "max_upload_bytes": 15 * 1024 * 1024,
        "notes": [
            "All processing is intended to remain local to this machine.",
            "An operating-system firewall should still be configured to block outbound traffic when the environment is isolated.",
        ],
    }


@app.get("/api/models")
def get_models() -> dict[str, Any]:
    try:
        model_items = list_models()
        return {"models": [model.name for model in model_items], "warnings": []}
    except RuntimeError as exc:
        return {"models": [], "warnings": [str(exc)]}


@app.get("/api/ollama/models")
def ollama_models() -> dict[str, Any]:
    try:
        model_items = list_models()
        return {"models": [model.to_dict() for model in model_items], "warning": None}
    except RuntimeError as exc:
        return {"models": [], "warning": str(exc)}


@app.post("/api/ollama/generate")
def ollama_generate(request: GenerateRequest) -> dict[str, Any]:
    try:
        response = generate_text(
            model=request.model,
            prompt=request.prompt,
            system=request.system,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        return {"model": request.model, "response": response}
    except RuntimeError as exc:
        return {"model": request.model, "response": "", "error": str(exc)}


@app.post("/api/ollama/chat")
def ollama_chat(request: ChatRequest) -> dict[str, Any]:
    try:
        response = chat_completion(
            model=request.model,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        return {"model": request.model, "response": response}
    except RuntimeError as exc:
        return {"model": request.model, "response": "", "error": str(exc)}


@app.post("/api/documents/upload")
async def upload_document_handler(file: UploadFile = File(...)) -> dict[str, Any]:
    if file.filename is None or not file.filename.strip():
        raise HTTPException(status_code=400, detail="A file name is required.")
    try:
        uploaded = upload_document(file.filename, await file.read())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return uploaded


@app.get("/api/documents")
def list_document_files() -> dict[str, Any]:
    return {"documents": list_documents()}


@app.delete("/api/documents/{document_id}")
def delete_document_handler(document_id: str) -> dict[str, Any]:
    deleted = delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"status": "deleted", "document_id": document_id}


@app.post("/api/search")
def search_documents_handler(request: SearchRequest) -> dict[str, Any]:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="A query is required.")
    results = search_documents(request.query, limit=request.limit)
    return {"query": request.query, "results": results}


@app.get("/api/artifacts")
def list_artifacts_endpoint() -> dict[str, Any]:
    return {"artifacts": list_artifacts()}


@app.post("/api/artifacts/generate")
def generate_report_artifact_endpoint(request: dict[str, Any]) -> dict[str, Any]:
    title = request.get("title")
    summary = request.get("summary")
    task_id = request.get("task_id")
    if not title or not summary:
        raise HTTPException(status_code=400, detail="title and summary are required.")
    artifact = generate_report_artifact(task_id or "manual", str(title), str(summary), request.get("details"))
    return artifact


@app.get("/api/artifacts/{artifact_id}/download")
def download_artifact_endpoint(artifact_id: str) -> FileResponse:
    try:
        artifact = fetch_artifact(artifact_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(path=artifact["path"], filename=artifact["file_name"], media_type=artifact["mime_type"])


@app.get("/api/workflows/examples")
def list_example_workflows() -> dict[str, Any]:
    return {"workflows": EXAMPLE_WORKFLOWS}


@app.post("/api/workflows/examples/{workflow_id}")
def create_example_workflow_endpoint(workflow_id: str) -> dict[str, Any]:
    try:
        workflow_task = create_example_workflow(workflow_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return workflow_task


@app.get("/api/tools")
def list_tools() -> dict[str, Any]:
    return {"tools": TOOL_REGISTRY.list()}


@app.post("/api/tasks")
def create_task_endpoint(request: TaskCreateRequest) -> dict[str, Any]:
    if not request.summary.strip():
        raise HTTPException(status_code=400, detail="A task summary is required.")
    task = create_task(
        summary=request.summary,
        task_type=request.task_type,
        preferred_model=request.preferred_model,
        query=request.query,
    )
    return task


@app.get("/api/tasks")
def list_tasks_endpoint() -> dict[str, Any]:
    return {"tasks": list_tasks()}


@app.get("/api/tasks/{task_id}")
def get_task_endpoint(task_id: str) -> dict[str, Any]:
    try:
        return fetch_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/tasks/{task_id}/execute")
def execute_task_endpoint(
    task_id: str,
    request: TaskExecuteRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, Any]:
    _validate_authorization_header(authorization, request.tool_name)
    try:
        task = execute_task(
            task_id=task_id,
            tool_name=request.tool_name,
            arguments=request.arguments,
            query=request.query,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return task


@app.get("/api/healthcheck")
def healthcheck() -> dict[str, Any]:
    return {
        "status": "ok",
        "backend": "SovereignAI",
        "offline_mode": OFFLINE_MODE,
        "tasks": [],
    }
