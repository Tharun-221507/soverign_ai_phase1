# SovereignAI

SovereignAI is a local-first AI workbench designed for confidential, on-premises knowledge work. This prototype focuses on local model discovery, document intelligence, and secure local execution patterns.

## Current status

The project now includes the local model, document, workflow, artifact, and security/offline posture foundations. The implementation remains incremental and has been validated through backend tests as it evolves.

### Included in the current build

- FastAPI backend with health, status, model, document, task, artifact, and security endpoints
- Local Ollama model discovery and direct generation/chat endpoints
- SQLite-backed document storage and local retrieval search
- Task/workflow state tracking with approved tool execution and audit history
- Report artifact generation and downloadable outputs for example workflows
- Local/offline mode configuration and security status reporting
- Automated backend tests covering core workflows and offline posture

## Local environment requirements

- Python 3.11+
- Node.js 18+
- Ollama installed and running on localhost:11434
- Optional local firewall configuration for outbound traffic restriction

## Quick start

Backend:

```bash
cd backend
python -m pip install -r requirements.txt
SOVEREIGNAI_OFFLINE_MODE=true python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

## Offline deployment guidance

This project is designed for a local-only workflow. All inference, document work, storage, and artifact generation remain on the local machine unless the configuration explicitly changes.

Recommended posture:

- Keep Ollama on `http://127.0.0.1:11434`
- Leave `SOVEREIGNAI_OFFLINE_MODE=true` for isolated deployments
- Restrict outbound firewall access from the host after all required dependencies and models are installed
- Use the `/api/security/status` endpoint to confirm the local-only configuration

If stricter operation is required, add a tool-auth token with:

```bash
SOVEREIGNAI_REQUIRE_TOOL_AUTH=true
SOVEREIGNAI_API_TOKEN=replace-with-local-only-token
```

The backend will then require the `Authorization: Bearer <token>` header for tool execution.

## Verified local inference

The local Ollama API was tested directly with the installed `qwen2.5:3b` model and returned a real response:

> Qwen is now ready to assist you.

## Final verification summary

The project was validated locally with:

- Backend tests: 17 passed
- Frontend production build: successful
- Runtime checks: backend and frontend served successfully on localhost
- Local model validation: `qwen2.5:3b` responded successfully through Ollama

## Notes

- The prototype uses local resources only and does not depend on external AI APIs for inference.
- Application-level configuration does not replace OS-level firewall controls for a fully isolated deployment.
- Security, storage isolation, and offline verification remain incremental but are now explicitly represented in the API and documentation.
