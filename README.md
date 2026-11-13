# Aether AI Personal Assistant

Aether is a local-first personal assistant built with Python. It connects to a configurable LLM provider and combines chat with persistent tasks, notes, reminders, and document utilities.

This is an educational MVP and portfolio project, not a production-ready or multi-user service.

## Features

- Chat with Google Gemini or a local Ollama server through a shared provider interface.
- Keep recent chat context during the current app session and persist conversation messages in SQLite.
- Create, list, complete, and delete tasks; create and manage notes and reminders using a controlled tool registry.
- Upload text, Markdown, CSV, JSON, or PDF files in the dashboard to preview extracted text and get a short extractive summary.
- Configure and validate providers from the Streamlit dashboard.
- Use the FastAPI endpoints for local development and integration.

Document uploads are processed by the application and are not exposed as arbitrary file-path tools to the model. The document summary is extractive: it selects text from the beginning of the file rather than asking an LLM to summarize it.
Scanned PDFs without an embedded text layer are not OCR-processed.

## Architecture

```text
app/
  api/            FastAPI routes
  core/           Assistant orchestration and conversation context
  memory/         SQLAlchemy models and SQLite persistence
  model_manager/  Provider configuration, status, and fallback
  providers/      Gemini and Ollama adapters
  tools/          Validated task, note, and reminder operations
  ui/             Streamlit dashboard
tests/            Pytest tests using temporary SQLite databases
```

## Requirements

- Python 3.10 or newer
- For Gemini: a Google AI Studio API key and network access. Google controls model availability, quotas, and pricing; check its [current model list](https://ai.google.dev/gemini-api/docs/models) and terms before use.
- For Ollama: an independently installed and running [Ollama server](https://ollama.com/), plus a model downloaded locally. Ollama is optional.

## Run locally

From the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` as needed. `GEMINI_API_KEY` may be left blank if you plan to use Ollama. `GEMINI_MODEL`, `OLLAMA_MODEL`, and `OLLAMA_HOST` select the provider models and local server.

Start the dashboard:

```powershell
python -m app.main --mode ui
```

Start the API and dashboard together:

```powershell
python -m app.main --mode both
```

By default, the API binds to `127.0.0.1:8000` and the dashboard to `127.0.0.1:8501`. Open <http://127.0.0.1:8501> for the dashboard and <http://127.0.0.1:8000/docs> for the local API documentation.

## Connect Google Gemini

In the dashboard, open **Proveedores**, select **Crear API key en Google AI Studio**, and create a key on [Google AI Studio](https://aistudio.google.com/api-keys). Return to Aether, paste the key, then choose **Conectar con Google Gemini**. The app validates it before selecting Gemini.

Alternatively, an administrator can put a server key in `.env` as `GEMINI_API_KEY`. A server key is shared by the app process and its usage is subject to Google's terms and quotas. A key entered in the dashboard is held in that Streamlit session's memory; it is not saved in the SQLite database or `.env`.

## Data and privacy

- SQLite stores chat messages, tasks, notes, and reminders locally in `aether.db` by default.
- Database contents are not encrypted by the app. Do not store sensitive information unless you have secured the host and its files.
- When Gemini is selected, prompts and relevant conversation context are sent to Google's API. Ollama requests go to the configured Ollama server.
- Do not commit `.env`, API keys, database files, uploaded files, or logs. `.gitignore` excludes local secrets and generated data; review `git status` before publishing.
- The API has no authentication and is intended for local development only. Do not bind it to a public or untrusted network.

## Tests

Run the suite with:

```powershell
pytest -q
```

Tests use temporary SQLite databases so they do not modify the developer's local application database. Provider tests use mocks and do not require live Gemini or Ollama credentials.

## Current limitations

- There are no user accounts, API authentication, or multi-user data isolation.
- Chat history is persisted, but only recent messages in the current assistant session are sent as context; previous sessions are not automatically loaded into a new chat.
- The local Ollama server and selected model must be installed and running by the user.
- Reminders are stored and displayed; the app does not run a background notification scheduler.
- Uploaded documents are processed for the current dashboard interaction and are not indexed or retained for later retrieval.
- Model IDs and provider quotas can change. Select a currently supported model in `.env` and check the provider's documentation.

## Roadmap

- Add authenticated API access and explicit user/session isolation before supporting remote or multi-user use.
- Load and manage saved conversation sessions.
- Add scheduled reminder delivery.
- Add document storage and retrieval (RAG) as an optional feature.
- Expand provider and tool integration with focused tests.

## License

No license is currently included. Add a license before inviting reuse or contributions so the terms are explicit.
