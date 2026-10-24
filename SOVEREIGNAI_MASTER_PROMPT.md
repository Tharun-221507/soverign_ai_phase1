# SOVEREIGNAI — COMPLETE APPLICATION BUILDER

## 1. ROLE

You are a senior software architect, full-stack developer, AI engineer, security engineer, and test engineer.

Your task is to BUILD a complete, functional application named SovereignAI inside the current VS Code workspace.

Do not stop after explaining the architecture, generating a folder structure, or writing a few example files.

Inspect the existing workspace, implement the application, integrate its components, execute appropriate tests, fix errors, and document the final result.

Work incrementally. Preserve existing useful code. Do not overwrite files blindly.

## 2. PROJECT OBJECTIVE

Build SovereignAI, a self-hosted AI workbench for confidential industrial, engineering, public-sector, and government knowledge work.

The application must allow authorized users to:

- Interact with locally hosted AI models.
- Upload and analyze confidential documents.
- Ask questions about private document collections.
- Retrieve relevant evidence from local knowledge sources.
- Process supported document and image formats.
- Select appropriate locally available models.
- Execute approved tools through controlled workflows.
- Generate reports and other useful deliverables.
- Inspect task progress, evidence, tool execution, and verification results.
- Operate without external AI APIs or external data transmission when configured for offline deployment.

Privacy, correctness, reliability, maintainability, and transparent execution are core requirements.

Do not claim that an implementation is air-gapped merely because it uses Ollama or a local database. Actual network isolation must be enforced and verified separately.

## 3. DEVELOPMENT ENVIRONMENT

Target environment:

- Operating system: Windows 11
- IDE: Visual Studio Code
- Python: 3.11 or newer
- Local model runtime: Ollama
- Processor: Intel Core i5 12th Generation
- GPU: NVIDIA RTX 3050, 4 GB VRAM
- RAM: 16 GB
- Available disk space: More than 30 GB

Inspect the actual installed versions and environment before selecting dependencies.

Account for limited GPU memory.

Prefer compatible quantized models and avoid loading multiple large models simultaneously.

Do not assume that a particular model is installed, supports vision, or fits in available memory. Discover installed models and verify capabilities.

Do not download large models or install system-level components without informing the user and obtaining approval when needed.

## 4. TECHNOLOGY STACK

Use the following stack unless workspace inspection reveals a concrete compatibility problem.

Frontend:
- React
- TypeScript
- Vite
- Tailwind CSS
- A suitable accessible component library

Backend:
- Python
- FastAPI
- Pydantic
- Uvicorn

AI integration:
- Ollama API
- Local language models
- Local embedding models
- Capability-aware model routing

Agent orchestration:
- LangGraph when its complexity is justified
- Explicit workflow states
- Controlled tool execution
- Structured execution traces

Retrieval:
- Local document extraction
- Configurable text chunking
- Local embeddings
- Qdrant or FAISS, selected according to operational needs
- Source metadata and document references

Storage:
- SQLite for the initial single-machine prototype
- SQLAlchemy or an equivalent maintainable data-access layer
- A migration path to PostgreSQL where necessary

Document processing:
- PyMuPDF for PDFs
- python-docx for DOCX
- openpyxl for XLSX
- python-pptx for PPTX
- Standard Python CSV processing
- A compatible local OCR engine for scanned documents

Testing:
- pytest
- FastAPI test client
- Frontend tests using an appropriate testing framework
- Integration tests
- Security-focused tests

Use maintained, compatible package versions. Avoid unnecessary dependencies.

## 5. REQUIRED APPLICATION MODULES

Implement the following modules as working application features.

### MODULE A: Dashboard

Create a professional dashboard showing:

- Application status
- Local model availability
- Available storage information where supported
- Document-library statistics
- Recent tasks
- Recent generated files
- Task success and failure indicators
- Offline-mode configuration status
- Clear warnings when a component is unavailable

All displayed status values must come from actual backend state.

Do not use fake metrics or permanently hardcoded success indicators.

### MODULE B: AI Chat Workspace

Implement:

- Conversation creation
- Conversation history
- User messages and AI responses
- Streaming responses where supported
- Local model selection
- Model availability indicators
- Error and timeout handling
- Stop-generation functionality where supported
- Copy-response functionality
- Clear conversation controls
- Evidence and execution-summary panels

Keep the interface responsive and usable on ordinary laptop hardware.

### MODULE C: Local Model Manager

Implement:

- Discover installed Ollama models
- Display model names and availability
- Allow the user to select a model
- Configure task-to-model routing
- Handle unavailable models
- Handle model-loading and inference errors
- Support configurable inference parameters
- Provide a compatible fallback only when explicitly configured
- Record model selection and routing reasons

Do not claim a model has been downloaded or loaded unless its actual status confirms this.

Provide clear instructions for adding models manually in an offline environment.

### MODULE D: Document Library

Support implemented document types, initially:

- PDF
- DOCX
- TXT
- CSV
- XLSX
- PPTX
- PNG
- JPG and JPEG

Implement:

- File upload
- File validation
- File-size limits
- File type validation
- Document listing
- Processing status
- Extraction status
- Metadata storage
- Document deletion
- Index deletion when a document is removed
- Clear processing errors

Treat uploaded files as untrusted input.

Prevent path traversal and unsafe filename handling.

Do not execute uploaded files.

For formats that cannot be processed, explain the limitation rather than silently ignoring the file.

### MODULE E: Private RAG

Implement the complete retrieval pipeline:

1. Receive an authorized document.
2. Extract text and supported metadata.
3. Apply local OCR where configured.
4. Split the content into meaningful chunks.
5. Generate embeddings using a local model.
6. Store chunks, embeddings, and source metadata locally.
7. Retrieve relevant chunks for a question.
8. Optionally rerank results if a suitable local reranker is available.
9. Generate a response grounded in retrieved evidence.
10. Attach available source references.
11. Detect insufficient evidence and communicate uncertainty.

Include:

- Configurable chunk size and overlap
- Retrieval limits
- Duplicate-document handling
- Indexing status
- Index persistence
- Document-to-chunk traceability
- Error recovery
- Re-indexing support
- Document deletion and corresponding index cleanup

Never invent citations, page numbers, quotations, or retrieved passages.

If evidence is insufficient, say so.

Do not send document content or embeddings to external services.

### MODULE F: Agent Workflow Engine

Create an observable workflow with the following states:

- RECEIVED
- VALIDATING
- PLANNING
- RETRIEVING
- EXECUTING
- VERIFYING
- COMPLETED
- PARTIALLY_COMPLETED
- BLOCKED
- FAILED

Not every task needs every state.

Implement:

- Task classification
- Concise task planning
- Dependency tracking
- Model selection
- Approved tool execution
- Intermediate result inspection
- Verification
- Controlled retries
- Failure reporting
- Execution history

Use LangGraph if appropriate for managing stateful workflows.

Do not implement unrestricted autonomous execution.

The model may propose tool calls, but application code must validate and authorize them.

### MODULE G: Approved Tools

Implement a registry of explicitly approved tools.

Initial tools may include:

- Document search
- Document metadata lookup
- Text extraction
- CSV inspection
- Basic calculations
- Statistical summaries
- Report generation
- File validation

Every tool must have:

- A defined name
- A description
- A validated input schema
- An authorization check
- An execution handler
- A defined result structure
- Error handling
- An execution record

Do not expose arbitrary shell execution as an unrestricted model tool.

### MODULE H: Restricted Code Execution

Implement this module only when an appropriate isolation mechanism is available.

Preferred approach:
- Docker container with no network access
- Restricted filesystem mounts
- Resource limits
- Execution timeout
- Non-privileged user
- No host Docker socket exposure to the model
- Explicit control of permitted inputs and outputs

If Docker or another suitable isolation mechanism is unavailable, report the limitation and leave the feature disabled until a secure alternative is configured.

Do not describe an ordinary subprocess as a secure sandbox.

Validate generated code and execution parameters.

Never execute code directly because a language model requests it.

### MODULE I: Multimodal Processing

Implement supported local image-processing workflows.

Features may include:

- OCR
- Image metadata inspection
- Vision-language model integration
- Scanned-document extraction
- Image-to-document retrieval
- Technical image descriptions

Check actual model compatibility before routing images to a model.

Do not claim full engineering drawing understanding unless it has been demonstrated through appropriate tests.

Treat image and document contents as untrusted data.

### MODULE J: Deliverable Generation

Generate supported outputs:

- TXT
- JSON
- CSV
- DOCX
- PDF
- XLSX
- PPTX

Use suitable document-generation libraries.

Implement:

- Output directory management
- Safe filenames
- File validation
- Clear generation status
- Error reporting
- Download endpoints
- Provenance metadata where appropriate

Do not claim an artifact exists until its creation has been verified.

### MODULE K: Security and Access Control

Implement security appropriate for the deployment model.

Include:

- Authentication before multi-user or network-accessible deployment
- Authorization for protected operations
- Secure session handling where applicable
- File access restrictions
- Request validation
- Upload limits
- Safe error responses
- Secret management
- Audit logging
- Configurable retention
- Secure deletion behavior where supported
- Dependency review
- No unnecessary telemetry

Do not hardcode passwords, API keys, tokens, or encryption secrets.

Do not expose the backend directly to an untrusted network.

Do not treat CORS as an authentication or network-isolation mechanism.

Do not log confidential document contents or entire prompts by default.

Keep detailed operational logs separate from sensitive user content.

### MODULE L: Offline Deployment

Design the application to operate offline after dependencies and model files have been provisioned.

Implement:

- Local model access
- Local embeddings
- Local document processing
- Local vector storage
- Local database storage
- Local artifact generation
- Clear configuration for external network restrictions

Create an offline deployment guide.

Identify any components that require prior downloading or provisioning.

Document how to install dependencies and models before isolation.

Do not claim complete network isolation from application-level settings alone.

Explain how to apply operating-system firewall rules and verify outbound connectivity.

Test that confidential data is not transmitted to external services during the configured offline workflow.

## 6. REASONING AND AUDITABILITY

Use structured, auditable execution summaries rather than exposing hidden chain-of-thought.

For each task, record appropriate fields:

- Task ID
- Task summary
- Current workflow state
- Concise plan summary
- Selected model
- Model-selection reason
- Sources retrieved
- Tool calls
- Actual tool outcomes
- Verification checks
- Errors and retries
- Assumptions
- Uncertainties
- Final status
- Output artifact locations

Keep logs proportional to the sensitivity of the operation.

Do not fabricate intermediate results or tool executions.

Do not treat a model-generated success message as proof that an operation succeeded.

Verify results using actual backend responses, filesystem checks, test results, or other appropriate independent checks.

## 7. API DESIGN

Design clear, versioned FastAPI endpoints.

Include appropriate endpoints for:

- Health checks
- Application status
- Model listing
- Model configuration
- Chat
- Conversation history
- Document upload
- Document listing
- Document deletion
- Document processing status
- Knowledge-base search
- Agent task creation
- Agent task status
- Execution-trace retrieval
- Artifact listing
- Artifact downloads
- User authentication where applicable

Use request and response schemas.

Validate inputs and return appropriate HTTP status codes.

Add timeouts and controlled error handling.

Avoid exposing internal exception details to users.

Ensure protected endpoints enforce authentication and authorization.

Document the API with FastAPI's OpenAPI support.

Do not create endpoints that claim functionality before the underlying feature exists.

## 8. DATABASE DESIGN

Design the database according to actual requirements.

Potential entities include:

- Users
- Conversations
- Messages
- Documents
- DocumentChunks
- Tasks
- TaskEvents
- ToolExecutions
- ModelConfigurations
- Artifacts
- AuditEvents

Avoid storing the same information unnecessarily.

Implement appropriate relationships, constraints, indexes, and timestamps.

Use migrations or a documented schema initialization process.

Keep document files and vector indexes consistent with database metadata.

Handle interrupted indexing and document deletion safely.

Do not store secrets in ordinary application tables.

## 9. FRONTEND DESIGN

Build a polished, professional interface suitable for industrial and government knowledge work.

Use a clear visual hierarchy.

Required pages:

- Dashboard
- AI Workspace
- Document Library
- Knowledge Search
- Model Manager
- Task Monitor
- Generated Files
- Settings

The interface must include:

- Loading indicators
- Empty states
- Error states
- Form validation
- Accessible controls
- Responsive layout
- Task status indicators
- Source-reference panels
- Execution-history panels

Avoid excessive animations and unnecessary visual effects.

Ensure every visible action is connected to a working backend operation.

Do not implement fake buttons, dummy search results, or simulated AI responses as production functionality.

If a feature is not yet implemented, label it clearly.

## 10. REQUIRED EXAMPLE WORKFLOWS

Implement and test the following three workflows.

### Workflow A: Inspection Report Analysis

Input:
- Inspection report
- Applicable operating procedure

Actions:
- Extract document content
- Retrieve relevant requirements
- Compare findings against the available evidence
- Produce a structured technical summary
- Generate a DOCX approval note
- Verify source references and the output file

Do not invent safety violations or approve consequential actions automatically.

### Workflow B: Local CSV Analysis

Input:
- Authorized CSV file
- Analysis requirements

Actions:
- Inspect the dataset
- Identify missing values
- Calculate descriptive statistics
- Generate a reproducible analysis script when required
- Execute code only within the configured restricted environment
- Validate the output
- Generate a summary report

Do not claim execution succeeded without verified results.

### Workflow C: Engineering Drawing Analysis

Input:
- Engineering drawing
- Related maintenance manual

Actions:
- Apply supported local OCR and image analysis
- Retrieve relevant manual sections
- Cross-reference available evidence
- Identify uncertainties
- Generate a technical summary

Do not invent dimensions, component identities, or maintenance requirements.

## 11. TESTING REQUIREMENTS

Create automated tests for:

- Configuration loading
- Ollama connectivity and error handling
- Model discovery
- Model routing
- Document extraction
- Invalid file uploads
- RAG indexing
- Retrieval relevance
- Source-reference integrity
- Document deletion
- Tool argument validation
- Authorization
- Artifact generation
- API error handling
- Workflow state transitions
- Offline-mode behavior
- Network-isolation verification procedures

Use mocks for unit tests when real models are not required.

Use integration tests with actual local components when available.

Mark tests that require installed models, GPU resources, Docker, or other optional infrastructure.

Do not report mocked tests as proof of successful real-model inference.

Do not skip failed tests without documenting why.

After each implementation phase:

1. Run the relevant tests.
2. Inspect the failures.
3. Fix the underlying issues.
4. Re-run the affected tests.
5. Record the results.
6. Proceed when the phase meets its acceptance criteria.

## 12. IMPLEMENTATION WORKFLOW

Follow this sequence.

PHASE 0 — Workspace Inspection

- Inspect the current workspace.
- Check the Python and Node.js environments.
- Check whether Ollama is installed and running.
- Inspect installed local models.
- Identify existing code and dependencies.
- Produce a concise implementation plan.
- Do not delete or overwrite useful files.

PHASE 1 — Foundation

- Create the backend structure.
- Configure the frontend.
- Add environment configuration.
- Implement health checks.
- Connect the frontend to the backend.
- Add basic automated tests.

PHASE 2 — Local AI

- Integrate Ollama.
- Implement model discovery.
- Implement model selection.
- Add chat endpoints.
- Verify actual local inference.

PHASE 3 — Document Intelligence

- Implement uploads and extraction.
- Add document metadata storage.
- Implement local embeddings.
- Add vector indexing.
- Implement retrieval and source references.

PHASE 4 — Agent Workflows

- Implement task planning.
- Add workflow state management.
- Integrate approved tools.
- Add execution traces.
- Implement verification and controlled recovery.

PHASE 5 — Deliverables

- Implement report generation.
- Add artifact storage and downloads.
- Verify output files.
- Implement the three example workflows.

PHASE 6 — Security

- Enforce permissions.
- Restrict tool access.
- Configure protected storage.
- Implement appropriate isolation controls.
- Verify offline behavior.
- Document any unresolved security limitations.

PHASE 7 — Frontend Completion

- Complete the dashboard.
- Complete the chat workspace.
- Complete the document library.
- Complete model management.
- Complete task monitoring.
- Complete artifact management.
- Connect all implemented controls to real backend functionality.

PHASE 8 — Final Verification

- Run backend tests.
- Run frontend tests.
- Run integration tests.
- Verify setup and startup instructions.
- Fix discovered defects.
- Review dependency and security limitations.
- Prepare the final project report.

## 13. OPERATING RULES FOR THE VS CODE AGENT

- Work directly in the current workspace.
- Inspect before editing.
- Use small, coherent implementation steps.
- Explain the objective of each phase briefly.
- Make actual code changes rather than only describing them.
- Use the terminal for appropriate setup, execution, and testing.
- Request approval before destructive commands, large downloads, system-wide changes, or sensitive operations.
- Never overwrite user data without permission.
- Keep configuration secrets out of source control.
- Do not fabricate test results.
- Do not silently replace a required technology with a different one.
- If a dependency or feature is unavailable, explain the limitation and implement a safe alternative only when appropriate.
- Keep a progress checklist in PROJECT_STATUS.md.
- Update the README.md as the application evolves.
- Record unresolved issues and incomplete requirements.
- Do not mark a phase complete until its acceptance criteria have been verified.

## 14. COMPLETION CRITERIA

The application is not complete merely because the frontend renders or the backend starts.

A feature is complete only when:

1. Its code is implemented.
2. Its inputs are validated.
3. Its success and failure paths are handled.
4. Its relevant tests pass.
5. Its frontend integration works where applicable.
6. Its output has been verified.
7. Its limitations are documented.

At the end, report:

- Implemented features
- Features verified through real execution
- Features verified only through mocks
- Features not implemented
- Test results
- Commands required to start the application
- Required local model setup
- Security limitations
- Offline deployment requirements
- Known issues
- Recommended next steps

Never describe unimplemented functionality as complete.

## 15. FIRST ACTION

Begin with PHASE 0.

Inspect the current VS Code workspace, the Python environment, Node.js availability, Ollama status, installed local models, and existing project files.

Then create or update PROJECT_STATUS.md with the implementation checklist and proposed architecture.

Proceed to PHASE 1 after the inspection.

Do not attempt to generate the entire codebase in a single enormous response.

Implement, test, verify, and refine the application incrementally until the available acceptance criteria are satisfied.