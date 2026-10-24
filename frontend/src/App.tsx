import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent, type ReactNode } from 'react'
import './App.css'

type TabKey =
  | 'dashboard'
  | 'workspace'
  | 'documents'
  | 'search'
  | 'models'
  | 'tasks'
  | 'artifacts'
  | 'settings'

type SystemState = {
  status: string
  environment: string
  python_version: string
  node_version: string | null
  offline_mode: boolean
  ollama_available: boolean
  ollama_version: string | null
  models: string[]
  warnings: string[]
}

type DocumentItem = {
  id: string
  original_name: string
  stored_name: string
  extension: string
  size_bytes: number
  uploaded_at: string
  file_path: string
  status: string
  metadata: string
}

type TaskItem = {
  id: string
  summary: string
  task_type: string
  workflow_state: string
  selected_model: string
  model_selection_reason: string
  evidence: Array<{ source: string; reference: string; relevance: unknown }>
  tool_calls: Array<{ tool_name: string; arguments?: Record<string, unknown>; result?: unknown; status?: string }>
  verification_results: Array<{ check: string; status: string; details: string }>
  execution_history: Array<{ state: string; timestamp: string; message: string }>
  artifacts: Array<{ name: string; details: unknown }>
  created_at: string
  updated_at: string
}

type ArtifactItem = {
  id: string
  task_id: string
  title: string
  type: string
  file_name: string
  path: string
  mime_type: string
  size_bytes: number
  created_at: string
}

type SecurityState = {
  offline_mode: boolean
  tool_auth_required: boolean
  local_only: boolean
  allowed_network: string[]
  allowed_extensions: string[]
  max_upload_bytes: number
  notes: string[]
}

type WorkflowExample = {
  id: string
  name: string
  description: string
  required_inputs: string[]
  actions: string[]
  task_type: string
}

const tabs: { key: TabKey; label: string }[] = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'workspace', label: 'AI Workspace' },
  { key: 'documents', label: 'Document Library' },
  { key: 'search', label: 'Knowledge Search' },
  { key: 'models', label: 'Model Manager' },
  { key: 'tasks', label: 'Task Monitor' },
  { key: 'artifacts', label: 'Generated Files' },
  { key: 'settings', label: 'Settings' },
]

const startTaskTypes = ['general_reasoning', 'document_retrieval', 'summarization', 'analysis']

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options)
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('dashboard')
  const [system, setSystem] = useState<SystemState | null>(null)
  const [models, setModels] = useState<string[]>([])
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [tasks, setTasks] = useState<TaskItem[]>([])
  const [artifacts, setArtifacts] = useState<ArtifactItem[]>([])
  const [security, setSecurity] = useState<SecurityState | null>(null)
  const [workflows, setWorkflows] = useState<WorkflowExample[]>([])
  const [searchQuery, setSearchQuery] = useState('confidential workflow')
  const [searchResults, setSearchResults] = useState<Array<Record<string, unknown>>>([])
  const [taskSummary, setTaskSummary] = useState('Review the local knowledge base and produce a cautious summary.')
  const [taskType, setTaskType] = useState('general_reasoning')
  const [uploading, setUploading] = useState(false)
  const [isBusy, setIsBusy] = useState<string>('')
  const [error, setError] = useState('')

  const modelTagList = useMemo(() => (system?.models?.length ? system.models : models), [system, models])

  const refreshAll = async () => {
    try {
      const [status, modelData, docData, taskData, artifactData, securityData, workflowData] = await Promise.all([
        fetchJson<SystemState>('/api/status'),
        fetchJson<{ models: string[]; warnings: string[] }>('/api/models'),
        fetchJson<{ documents: DocumentItem[] }>('/api/documents'),
        fetchJson<{ tasks: TaskItem[] }>('/api/tasks'),
        fetchJson<{ artifacts: ArtifactItem[] }>('/api/artifacts'),
        fetchJson<SecurityState>('/api/security/status'),
        fetchJson<{ workflows: WorkflowExample[] }>('/api/workflows/examples'),
      ])
      setSystem(status)
      setModels(modelData.models)
      setDocuments(docData.documents)
      setTasks(taskData.tasks)
      setArtifacts(artifactData.artifacts)
      setSecurity(securityData)
      setWorkflows(workflowData.workflows)
      setError('')
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load SovereignAI data.')
    }
  }

  useEffect(() => {
    void refreshAll()
  }, [])

  const handleSearch = async (event: FormEvent) => {
    event.preventDefault()
    try {
      setIsBusy('search')
      const result = await fetchJson<{ query: string; results: Array<Record<string, unknown>> }>('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, limit: 5 }),
      })
      setSearchResults(result.results)
      setError('')
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Search failed.')
    } finally {
      setIsBusy('')
    }
  }

  const handleUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      setUploading(true)
      const formData = new FormData()
      formData.append('file', file)
      await fetchJson<{ id: string; filename: string; status: string; chunks: number }>('/api/documents/upload', {
        method: 'POST',
        body: formData,
      })
      await refreshAll()
      setError('')
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Upload failed.')
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  const handleCreateTask = async (event: FormEvent) => {
    event.preventDefault()
    try {
      setIsBusy('task-create')
      await fetchJson('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ summary: taskSummary, task_type: taskType, query: taskSummary }),
      })
      await refreshAll()
      setError('')
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Task creation failed.')
    } finally {
      setIsBusy('')
    }
  }

  const handleExecuteTask = async (taskId: string, toolName: string, argumentsObject: Record<string, unknown>) => {
    try {
      setIsBusy(`execute:${taskId}`)
      await fetchJson(`/api/tasks/${taskId}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool_name: toolName, arguments: argumentsObject, query: argumentsObject.query ?? taskSummary }),
      })
      await refreshAll()
      setError('')
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Task execution failed.')
    } finally {
      setIsBusy('')
    }
  }

  const handleWorkflowRun = async (workflowId: string) => {
    try {
      setIsBusy(`workflow:${workflowId}`)
      await fetchJson(`/api/workflows/examples/${workflowId}`, { method: 'POST' })
      await refreshAll()
      setError('')
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Workflow execution failed.')
    } finally {
      setIsBusy('')
    }
  }

  const renderDashboard = () => (
    <div className="page-stack">
      <section className="stats-grid">
        <article className="card">
          <span className="label">Backend</span>
          <strong>{system?.status ?? '—'}</strong>
          <small>{system?.environment ?? 'Local environment'}</small>
        </article>
        <article className="card">
          <span className="label">Python</span>
          <strong>{system?.python_version ?? '—'}</strong>
          <small>Runtime</small>
        </article>
        <article className="card">
          <span className="label">Node</span>
          <strong>{system?.node_version ?? '—'}</strong>
          <small>Frontend toolchain</small>
        </article>
        <article className="card">
          <span className="label">Offline mode</span>
          <strong>{system?.offline_mode ? 'Enabled' : 'Disabled'}</strong>
          <small>Local-only policy</small>
        </article>
      </section>

      <section className="panel-grid">
        <article className="panel">
          <h2>Local model status</h2>
          <ul className="list">
            <li><span>Ollama</span><strong>{system?.ollama_available ? 'Available' : 'Unavailable'}</strong></li>
            <li><span>Version</span><strong>{system?.ollama_version ?? 'Unknown'}</strong></li>
            <li><span>Installed models</span><strong>{modelTagList.length}</strong></li>
          </ul>
          {modelTagList.length > 0 ? (
            <div className="tag-list">{modelTagList.map((model) => <span key={model} className="tag">{model}</span>)}</div>
          ) : (
            <p className="muted">No local models detected yet.</p>
          )}
        </article>

        <article className="panel">
          <h2>Operational notes</h2>
          {system?.warnings && system.warnings.length > 0 ? (
            <ul className="warning-list">{system.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
          ) : (
            <p className="muted">No warnings at the moment.</p>
          )}
        </article>
      </section>
    </div>
  )

  const renderWorkspace = () => (
    <section className="page-card">
      <h2>AI Workspace</h2>
      <form onSubmit={handleCreateTask} className="inline-form">
        <label>
          Task summary
          <textarea value={taskSummary} onChange={(event) => setTaskSummary(event.target.value)} rows={4} />
        </label>
        <label>
          Task type
          <select value={taskType} onChange={(event) => setTaskType(event.target.value)}>
            {startTaskTypes.map((type) => <option key={type} value={type}>{type}</option>)}
          </select>
        </label>
        <button type="submit" className="primary-button" disabled={isBusy === 'task-create'}>
          {isBusy === 'task-create' ? 'Creating…' : 'Create task'}
        </button>
      </form>

      <div className="mini-grid">
        {workflows.map((workflow) => (
          <article key={workflow.id} className="mini-panel">
            <h3>{workflow.name}</h3>
            <p>{workflow.description}</p>
            <ul>
              {workflow.required_inputs.map((input) => <li key={input}>{input}</li>)}
            </ul>
            <button type="button" className="secondary-button" onClick={() => void handleWorkflowRun(workflow.id)} disabled={isBusy === `workflow:${workflow.id}`}>
              {isBusy === `workflow:${workflow.id}` ? 'Running…' : 'Run workflow'}
            </button>
          </article>
        ))}
      </div>
    </section>
  )

  const renderDocuments = () => (
    <section className="page-card">
      <h2>Document Library</h2>
      <div className="upload-row">
        <label className="upload-box">
          <input type="file" onChange={handleUpload} />
          <span>{uploading ? 'Uploading…' : 'Upload local document'}</span>
        </label>
      </div>
      {documents.length === 0 ? <p className="muted">No documents indexed yet.</p> : (
        <div className="list-table">
          {documents.map((document) => (
            <div key={document.id} className="table-row">
              <div>
                <strong>{document.original_name}</strong>
                <small>{document.extension} · {Math.max(1, Math.round(document.size_bytes / 1024))} KB</small>
              </div>
              <span>{document.status}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  )

  const renderSearch = () => (
    <section className="page-card">
      <h2>Knowledge Search</h2>
      <form onSubmit={handleSearch} className="search-form">
        <input value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Search local document corpus" />
        <button className="primary-button" type="submit" disabled={isBusy === 'search'}>{isBusy === 'search' ? 'Searching…' : 'Search'}</button>
      </form>
      {searchResults.length === 0 ? <p className="muted">No search results yet.</p> : (
        <div className="result-list">
          {searchResults.map((result, index) => (
            <article key={`${String(result.document_name ?? 'result')}-${index}`} className="result-item">
              <h3>{String(result.document_name ?? 'Document')}</h3>
              <p>{String(result.content ?? '')}</p>
              <small>Score: {String(result.score ?? 'n/a')}</small>
            </article>
          ))}
        </div>
      )}
    </section>
  )

  const renderModels = () => (
    <section className="page-card">
      <h2>Model Manager</h2>
      {modelTagList.length === 0 ? <p className="muted">No local models discovered.</p> : (
        <div className="tag-list large">{modelTagList.map((model) => <span key={model} className="tag">{model}</span>)}</div>
      )}
      <div className="model-summary">
        <strong>Ollama available:</strong> {system?.ollama_available ? 'Yes' : 'No'}
      </div>
      <div className="model-summary">
        <strong>Local-only policy:</strong> {system?.offline_mode ? 'Enabled' : 'Disabled'}
      </div>
    </section>
  )

  const renderTasks = () => (
    <section className="page-card">
      <h2>Task Monitor</h2>
      {tasks.length === 0 ? <p className="muted">No tasks recorded yet.</p> : (
        <div className="task-list">
          {tasks.map((task) => (
            <article key={task.id} className="task-item">
              <div className="task-header">
                <div>
                  <strong>{task.summary}</strong>
                  <small>{task.task_type} · {task.workflow_state}</small>
                </div>
                <button type="button" className="secondary-button" onClick={() => void handleExecuteTask(task.id, 'document_search', { query: task.summary, limit: 3 })} disabled={isBusy === `execute:${task.id}`}>
                  {isBusy === `execute:${task.id}` ? 'Running…' : 'Run document search'}
                </button>
              </div>
              <p>{task.model_selection_reason}</p>
              {task.verification_results.length > 0 ? (
                <ul className="check-list">
                  {task.verification_results.map((result, index) => (
                    <li key={`${result.check}-${index}`}>{result.check}: {result.status} — {result.details}</li>
                  ))}
                </ul>
              ) : null}
            </article>
          ))}
        </div>
      )}
    </section>
  )

  const renderArtifacts = () => (
    <section className="page-card">
      <h2>Generated Files</h2>
      {artifacts.length === 0 ? <p className="muted">No generated files yet.</p> : (
        <div className="artifact-list">
          {artifacts.map((artifact) => (
            <article key={artifact.id} className="artifact-item">
              <div>
                <strong>{artifact.title}</strong>
                <small>{artifact.file_name}</small>
              </div>
              <a href={`/api/artifacts/${artifact.id}/download`} target="_blank" rel="noreferrer" className="link-button">Download</a>
            </article>
          ))}
        </div>
      )}
    </section>
  )

  const renderSettings = () => (
    <section className="page-card">
      <h2>Settings</h2>
      {security ? (
        <div className="settings-grid">
          <div><strong>Offline mode</strong><p>{security.offline_mode ? 'Enabled' : 'Disabled'}</p></div>
          <div><strong>Tool auth</strong><p>{security.tool_auth_required ? 'Required' : 'Optional'}</p></div>
          <div><strong>Local-only</strong><p>{security.local_only ? 'Yes' : 'No'}</p></div>
          <div><strong>Max upload</strong><p>{Math.round(security.max_upload_bytes / (1024 * 1024))} MB</p></div>
        </div>
      ) : (
        <p className="muted">Security policy is loading.</p>
      )}
      <ul className="note-list">
        {(security?.notes ?? ['No local security notes available yet.']).map((note) => <li key={note}>{note}</li>)}
      </ul>
    </section>
  )

  const panels: Record<TabKey, ReactNode> = {
    dashboard: renderDashboard(),
    workspace: renderWorkspace(),
    documents: renderDocuments(),
    search: renderSearch(),
    models: renderModels(),
    tasks: renderTasks(),
    artifacts: renderArtifacts(),
    settings: renderSettings(),
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Secure local AI workbench</p>
          <h1>SovereignAI</h1>
        </div>
        <div className={`status-pill ${system?.status === 'ready' ? 'online' : 'offline'}`}>
          {system?.status ?? 'Checking'}
        </div>
      </header>

      {error ? <section className="alert"><strong>Connection warning:</strong> {error}</section> : null}

      <nav className="tabbar" aria-label="Primary navigation">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={activeTab === tab.key ? 'tab-button active' : 'tab-button'}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {panels[activeTab]}
    </main>
  )
}

export default App
