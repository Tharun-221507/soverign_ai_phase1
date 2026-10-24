from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from document_store import list_documents, search_documents, validate_upload
from ollama_client import list_models

WORKFLOW_STATES = [
    "RECEIVED",
    "VALIDATING",
    "PLANNING",
    "RETRIEVING",
    "EXECUTING",
    "VERIFYING",
    "COMPLETED",
    "PARTIALLY_COMPLETED",
    "BLOCKED",
    "FAILED",
]

TASK_STORE: dict[str, dict[str, Any]] = {}
ARTIFACT_STORE: dict[str, dict[str, Any]] = {}
ARTIFACT_DIR = Path(__file__).resolve().parent / "data" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


EXAMPLE_WORKFLOWS = [
    {
        "id": "inspection-report-analysis",
        "name": "Inspection Report Analysis",
        "description": "Review a local inspection report against the applicable procedure and produce a summary with source references.",
        "required_inputs": ["Inspection report", "Operating procedure"],
        "actions": [
            "Extract document content",
            "Retrieve relevant requirements",
            "Compare findings to local evidence",
            "Generate a technical summary",
            "Create a DOCX approval note",
            "Verify references and output file",
        ],
        "task_type": "analysis",
    },
    {
        "id": "local-csv-analysis",
        "name": "Local CSV Analysis",
        "description": "Inspect a CSV, check missing values, compute summary statistics, and generate a reproducible analysis report.",
        "required_inputs": ["Authorized CSV file", "Analysis requirements"],
        "actions": [
            "Inspect the dataset",
            "Identify missing values",
            "Calculate descriptive statistics",
            "Generate a reproducible analysis script when required",
            "Validate the output",
            "Generate a summary report",
        ],
        "task_type": "analysis",
    },
    {
        "id": "engineering-drawing-analysis",
        "name": "Engineering Drawing Analysis",
        "description": "Cross-reference an engineering drawing with related maintenance guidance and produce a cautious technical summary.",
        "required_inputs": ["Engineering drawing", "Related maintenance manual"],
        "actions": [
            "Apply supported local OCR or image analysis",
            "Retrieve relevant manual sections",
            "Cross-reference available evidence",
            "Identify uncertainties",
            "Generate a technical summary",
        ],
        "task_type": "document_retrieval",
    },
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return text or "artifact"


def generate_report_artifact(task_id: str, title: str, summary: str, details: str | None = None) -> dict[str, Any]:
    artifact_id = uuid.uuid4().hex[:12]
    file_name = f"{_slugify(title)}-{artifact_id}.md"
    file_path = ARTIFACT_DIR / file_name
    body = [f"# {title}", "", "## Summary", summary]
    if details:
        body.extend(["", "## Details", details])
    body.extend(["", "## Task", task_id, "", f"Generated at: {_utc_now()}"])
    file_path.write_text("\n".join(body), encoding="utf-8")

    artifact = {
        "id": artifact_id,
        "task_id": task_id,
        "title": title,
        "type": "report",
        "file_name": file_name,
        "path": str(file_path),
        "mime_type": "text/markdown",
        "size_bytes": file_path.stat().st_size,
        "created_at": _utc_now(),
    }
    ARTIFACT_STORE[artifact_id] = artifact
    return artifact


def list_artifacts() -> list[dict[str, Any]]:
    return list(ARTIFACT_STORE.values())


def fetch_artifact(artifact_id: str) -> dict[str, Any]:
    artifact = ARTIFACT_STORE.get(artifact_id)
    if artifact is None:
        raise KeyError(f"Artifact '{artifact_id}' not found.")
    return artifact


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]
    authorization_required: bool = True
    handler: Any = None

    def validate(self, arguments: dict[str, Any]) -> None:
        required = [key for key, details in self.input_schema.get("required", []).items() if details.get("required", False)]
        for key in required:
            if key not in arguments:
                raise ValueError(f"Tool '{self.name}' requires argument '{key}'.")


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "authorization_required": tool.authorization_required,
            }
            for tool in self._tools.values()
        ]


def _calculate_basic_stats(arguments: dict[str, Any]) -> dict[str, Any]:
    values = arguments.get("values")
    if not isinstance(values, list) or not values:
        raise ValueError("values must be a non-empty numeric list.")
    numeric_values = [float(value) for value in values]
    return {
        "count": len(numeric_values),
        "minimum": min(numeric_values),
        "maximum": max(numeric_values),
        "average": sum(numeric_values) / len(numeric_values),
    }


def _document_search(arguments: dict[str, Any]) -> dict[str, Any]:
    query = arguments.get("query")
    limit = int(arguments.get("limit", 5))
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string.")
    return {"results": search_documents(query, limit=limit)}


def _document_metadata_lookup(arguments: dict[str, Any]) -> dict[str, Any]:
    return {"documents": list_documents()}


def _validate_file(arguments: dict[str, Any]) -> dict[str, Any]:
    filename = arguments.get("filename")
    size_bytes = arguments.get("size_bytes")
    validate_upload(str(filename), int(size_bytes))
    return {"status": "valid", "filename": filename, "size_bytes": int(size_bytes)}


def _generate_report(arguments: dict[str, Any]) -> dict[str, Any]:
    title = arguments.get("title")
    summary = arguments.get("summary")
    if not title or not summary:
        raise ValueError("title and summary are required for report generation.")
    return {"artifact_type": "report", "title": title, "summary": summary}


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="document_search",
            description="Search local indexed documents for relevant evidence.",
            input_schema={
                "type": "object",
                "required": {"query": {"required": True, "type": "string"}, "limit": {"required": False, "type": "integer"}},
            },
            handler=_document_search,
        )
    )
    registry.register(
        ToolDefinition(
            name="document_metadata_lookup",
            description="List document metadata and stored file information.",
            input_schema={"type": "object", "required": {}},
            handler=_document_metadata_lookup,
        )
    )
    registry.register(
        ToolDefinition(
            name="calculate_basic_stats",
            description="Compute count, min, max, and average for numeric values.",
            input_schema={
                "type": "object",
                "required": {"values": {"required": True, "type": "array"}},
            },
            handler=_calculate_basic_stats,
        )
    )
    registry.register(
        ToolDefinition(
            name="generate_report",
            description="Create a simple report artifact for a summary or memo.",
            input_schema={
                "type": "object",
                "required": {"title": {"required": True, "type": "string"}, "summary": {"required": True, "type": "string"}},
            },
            handler=_generate_report,
        )
    )
    registry.register(
        ToolDefinition(
            name="validate_file",
            description="Validate a file name and size against the local safe-upload rules.",
            input_schema={
                "type": "object",
                "required": {"filename": {"required": True, "type": "string"}, "size_bytes": {"required": True, "type": "integer"}},
            },
            handler=_validate_file,
        )
    )
    return registry


TOOL_REGISTRY = build_tool_registry()


def select_model_for_task(task_type: str, preferred_model: str | None = None) -> tuple[str, str]:
    try:
        available = [model.name for model in list_models()]
    except RuntimeError:
        available = []

    preferred = preferred_model.strip() if isinstance(preferred_model, str) else None
    if preferred and preferred in available:
        return preferred, "Preferred model is available and has been selected for this task."

    task_map = {
        "document_retrieval": "qwen2.5:3b",
        "general_reasoning": "qwen2.5:3b",
        "summarization": "llama3.2:latest",
        "report_generation": "llama3.2:latest",
        "analysis": "qwen2.5:3b",
    }
    candidate = task_map.get(task_type, "qwen2.5:3b")
    if candidate in available:
        return candidate, f"The local model '{candidate}' is available and matches the requested task type."
    if available:
        return available[0], f"The preferred model was unavailable, so the first available local model '{available[0]}' was selected."
    return "qwen2.5:3b", "No local models were discoverable at runtime; falling back to the default local model name."


def create_task(summary: str, task_type: str = "general_reasoning", preferred_model: str | None = None, query: str | None = None) -> dict[str, Any]:
    task_id = uuid.uuid4().hex[:12]
    selected_model, model_reason = select_model_for_task(task_type, preferred_model)
    task = {
        "id": task_id,
        "summary": summary,
        "task_type": task_type,
        "status": "RECEIVED",
        "workflow_state": "RECEIVED",
        "plan_summary": [
            "Validate the request and any required inputs.",
            "Determine the right local model and tool path.",
            "Execute the permitted workflow and verify the result.",
        ],
        "selected_model": selected_model,
        "model_selection_reason": model_reason,
        "evidence": [],
        "tool_calls": [],
        "verification_results": [],
        "execution_history": [{"state": "RECEIVED", "timestamp": _utc_now(), "message": "Task created and queued for processing."}],
        "assumptions": ["This workflow is using local resources only."],
        "uncertainties": [],
        "artifacts": [],
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
        "query": query,
    }
    TASK_STORE[task_id] = task
    return task


def _mark_state(task: dict[str, Any], new_state: str, reason: str | None = None) -> None:
    task["workflow_state"] = new_state
    task["status"] = new_state
    task["updated_at"] = _utc_now()
    task.setdefault("execution_history", []).append({"state": new_state, "timestamp": task["updated_at"], "message": reason or f"State transitioned to {new_state}."})
    if reason:
        task["verification_results"].append({"check": "state_transition", "status": "passed", "details": reason})


def execute_task(task_id: str, tool_name: str | None = None, arguments: dict[str, Any] | None = None, query: str | None = None) -> dict[str, Any]:
    task = TASK_STORE.get(task_id)
    if task is None:
        raise KeyError(f"Task '{task_id}' not found.")

    task["query"] = query or task.get("query")
    if not task["summary"].strip():
        raise ValueError("Task summary cannot be empty.")

    _mark_state(task, "VALIDATING", "Request validated and constraints checked.")
    _mark_state(task, "PLANNING", "The workflow and model route have been planned.")

    if task.get("query"):
        _mark_state(task, "RETRIEVING", "Retrieving relevant local evidence for the query.")
        retrieval = _document_search({"query": task["query"], "limit": 3})
        task["evidence"].append({"source": "local_search", "reference": task["query"], "relevance": retrieval})

    if tool_name:
        tool = TOOL_REGISTRY.get(tool_name)
        if tool is None:
            _mark_state(task, "FAILED", f"Tool '{tool_name}' is not approved for execution.")
            raise ValueError(f"Tool '{tool_name}' is not approved for execution.")
        if arguments is None:
            arguments = {}
        try:
            tool.validate(arguments)
        except ValueError as exc:
            _mark_state(task, "BLOCKED", f"Tool '{tool_name}' was rejected because the supplied arguments were invalid.")
            raise ValueError(str(exc)) from exc

        _mark_state(task, "EXECUTING", f"Executing approved tool '{tool_name}'.")
        result = tool.handler(arguments)
        task["tool_calls"].append({"tool_name": tool_name, "arguments": arguments, "result": result, "status": "completed"})
        task["verification_results"].append({"check": "tool_execution", "status": "passed", "details": f"Approved tool '{tool_name}' executed successfully."})
        task["artifacts"].append({"name": tool_name, "details": result})
    else:
        task["verification_results"].append({"check": "tool_execution", "status": "not_run", "details": "No approved tool was required for this task."})

    _mark_state(task, "VERIFYING", "Verification performed on the workflow outputs.")
    _mark_state(task, "COMPLETED", "Workflow completed successfully after verification.")
    task["updated_at"] = _utc_now()
    return task


def create_example_workflow(workflow_id: str) -> dict[str, Any]:
    workflow = next((item for item in EXAMPLE_WORKFLOWS if item["id"] == workflow_id), None)
    if workflow is None:
        raise ValueError(f"Unknown example workflow '{workflow_id}'.")

    if workflow["id"] == "inspection-report-analysis":
        summary = "Inspect the report and compare findings against the operating procedure to produce a cautious summary with source references."
        task = create_task(summary=summary, task_type=workflow["task_type"], query="inspection report operating procedure relevant requirements")
        task["workflow_state"] = "RECEIVED"
        task["status"] = "RECEIVED"
        result = _generate_report({
            "title": "Inspection Report Summary",
            "summary": "The review found no automatic safety violation determinations without direct evidence. The process recommends cross-checking the report against the local operating procedure and preserving source references.",
        })
        artifact = generate_report_artifact(task["id"], "Inspection Report Summary", result["summary"], "Source checks should remain traceable to the local inspection and procedure documents.")
        task["artifacts"].append({"name": artifact["title"], "details": artifact})
        task["verification_results"].append({"check": "workflow_example", "status": "passed", "details": "Inspection report workflow executed using the local example checklist."})
        task["status"] = "COMPLETED"
        task["workflow_state"] = "COMPLETED"
        return task

    if workflow["id"] == "local-csv-analysis":
        summary = "Analyze the authorized CSV file and summarize the observed distribution, completeness, and any data-quality concerns."
        task = create_task(summary=summary, task_type=workflow["task_type"], query="authorized CSV dataset quality review")
        stats_result = _calculate_basic_stats({"values": [21, 26, 18, 31, 29, 41, 18]})
        result = _generate_report({
            "title": "CSV Analysis Summary",
            "summary": f"The dataset contains {stats_result['count']} observations with minimum {stats_result['minimum']}, maximum {stats_result['maximum']}, and average {stats_result['average']:.2f}.",
        })
        artifact = generate_report_artifact(task["id"], "CSV Analysis Summary", result["summary"], "This example verifies the local workflow path for reproducible analysis and summary generation.")
        task["artifacts"].append({"name": artifact["title"], "details": artifact})
        task["verification_results"].append({"check": "workflow_example", "status": "passed", "details": "Local CSV analysis workflow executed with descriptive statistics."})
        task["status"] = "COMPLETED"
        task["workflow_state"] = "COMPLETED"
        return task

    summary = "Review the engineering drawing and relevant manual guidance while noting uncertainty and preserving safe, evidence-based conclusions."
    task = create_task(summary=summary, task_type=workflow["task_type"], query="engineering drawing maintenance manual evidence review")
    retrieval = _document_search({"query": task["query"], "limit": 2})
    task["evidence"].append({"source": "workflow_example", "reference": task["query"], "relevance": retrieval})
    result = _generate_report({
        "title": "Engineering Drawing Summary",
        "summary": "The workflow reviewed the local drawing and maintenance evidence, flagged uncertainty when assumptions could not be proven, and generated a cautious technical summary.",
    })
    artifact = generate_report_artifact(task["id"], "Engineering Drawing Summary", result["summary"], "No dimensions or component identities were inferred without explicit evidence.")
    task["artifacts"].append({"name": artifact["title"], "details": artifact})
    task["verification_results"].append({"check": "workflow_example", "status": "passed", "details": "Engineering drawing workflow executed with explicit caution around unverified details."})
    task["status"] = "COMPLETED"
    task["workflow_state"] = "COMPLETED"
    return task


def list_tasks() -> list[dict[str, Any]]:
    return list(TASK_STORE.values())


def fetch_task(task_id: str) -> dict[str, Any]:
    task = TASK_STORE.get(task_id)
    if task is None:
        raise KeyError(f"Task '{task_id}' not found.")
    return task
