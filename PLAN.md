# Docs RAG Interface (Verba‑like) — Build Plan & Scaffolding

*A local, privacy‑first, Verba‑style document QA system with Ollama/OpenAI flexibility, URL/PDF ingestion, chat UI, and interaction history.*

---

## 0) Goals & Non‑Goals

**Goals**
- Local vector store (Chroma) with persistent disk.
- Ingest: file upload (PDF first; extensible to DOCX/MD/TXT), and URL fetch.
- Optionally use an LLM to analyze a page and extract PDF links; auto‑download and ingest those PDFs.
- Embeddings: pluggable providers → **Ollama** (e.g., `nomic-embed-text` or `mxbai-embed-large`) or **OpenAI** (`text-embedding-3-*`).
- Chat UI to interact with documents; display sources/citations; store chat history.
- Small, composable codebase: FastAPI (Python) backend, React (Vite + Tailwind) frontend.
- Runs locally via `docker compose` **or** Python/Node with a **virtual environment (venv)**.

**Non‑Goals (MVP)**
- Multi‑tenant auth, RBAC, or SSO.
- Fine‑tuning or long‑context streaming beyond standard RAG.
- Enterprise observability (can add later).

---

## 20) Quick Start (dev, no docker)

```bash
# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\\Scripts\\activate

# Install dependencies
pip install fastapi uvicorn[standard] sqlmodel chromadb httpx pymupdf pypdf beautifulsoup4 trafilatura python-multipart openai

# Copy env and configure
cp .env.example .env  # edit providers

# Run backend
uvicorn app:app --reload

# Start frontend in another shell
npm i && npm run dev
```

> **Note**: Using a `venv` is strongly recommended over bare‑metal installs. It ensures dependency isolation, reproducibility, and easier deployment to different machines or CI/CD pipelines.

---

**You now have a clear blueprint.** Start with M0→M1 and iterate. When you want, we can turn this into a real repo scaffold (files + minimal working code) in one go.

