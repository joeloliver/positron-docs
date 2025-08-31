# Document RAG Interface

A local, privacy-first document QA system with Ollama/OpenAI flexibility, URL/PDF ingestion, chat UI, and interaction history.

## Features

- 📄 **Document Upload**: Support for PDF, TXT, and MD files
- 🌐 **URL Ingestion**: Extract content from web pages with optional PDF extraction
- 🔍 **Semantic Search**: Vector-based document search using Chroma
- 💬 **Chat Interface**: Interactive chat with document context
- 📊 **Session Management**: Track and resume chat sessions
- 🔌 **Flexible Providers**: Support for both Ollama (local) and OpenAI embeddings/LLMs
- 🎨 **Modern UI**: Clean React interface with Tailwind CSS

## Prerequisites

- Python 3.9+
- Node.js 20.17+
- Ollama (if using local models)

## Quick Start

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd positron-docs

# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# - Choose embedding provider (ollama or openai)
# - Set API keys if using OpenAI
# - Configure Ollama models if using local
```

### 3. Install Ollama Models (if using Ollama)

```bash
# Install embedding model
ollama pull nomic-embed-text

# Install chat model
ollama pull llama3.2
```

### 4. Start the Backend

```bash
# Activate virtual environment if not already active
source .venv/bin/activate

# Run the FastAPI backend
uvicorn app:app --reload
```

The backend will be available at http://localhost:8000

### 5. Start the Frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173

## Project Structure

```
positron-docs/
├── app.py                 # Main FastAPI application
├── backend/
│   ├── config.py         # Configuration settings
│   ├── models.py         # Database and API models
│   ├── database.py       # Database setup
│   ├── embeddings.py     # Embedding providers
│   ├── vector_store.py   # Chroma vector store
│   ├── document_processor.py  # Document processing
│   └── llm.py           # LLM providers and chat engine
├── frontend/
│   ├── src/
│   │   ├── App.jsx      # Main React component
│   │   ├── api.js       # API client
│   │   └── index.css    # Tailwind styles
│   └── package.json
├── data/                 # Database and vector store
├── uploads/             # Uploaded documents
└── .env.example         # Environment template
```

## Usage

1. **Upload Documents**: Use the Upload tab to add PDF, TXT, or MD files
2. **Ingest URLs**: Enter a URL to extract and index web content
3. **Chat**: Ask questions about your documents in the Chat tab
4. **Search**: Find specific content across all documents
5. **Manage**: View and delete documents in the Documents tab

## API Endpoints

- `POST /api/upload` - Upload a document
- `POST /api/ingest_url` - Ingest content from URL
- `POST /api/chat` - Send chat message
- `GET /api/sessions` - List chat sessions
- `GET /api/sessions/{id}/messages` - Get session messages
- `POST /api/search` - Search documents
- `GET /api/documents` - List documents
- `DELETE /api/documents/{id}` - Delete document
- `GET /api/stats` - System statistics

## Configuration Options

### Embedding Providers

- **Ollama** (default): Local embeddings using models like `nomic-embed-text`
- **OpenAI**: Cloud-based embeddings using `text-embedding-3-*` models

### LLM Providers

- **Ollama**: Local models like `llama3.2`, `mistral`, etc.
- **OpenAI**: GPT models like `gpt-4o-mini`

### Storage

- **SQLite**: Document metadata and chat history
- **Chroma**: Vector embeddings with persistent disk storage

## Troubleshooting

### Backend Issues

```bash
# Check if Ollama is running (if using local models)
ollama list

# Verify Python dependencies
pip list

# Check logs
uvicorn app:app --reload --log-level debug
```

### Frontend Issues

```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Common Problems

1. **Ollama connection error**: Ensure Ollama is running (`ollama serve`)
2. **CORS errors**: Check that backend is running on port 8000
3. **Module not found**: Activate virtual environment before running backend
4. **npm permission errors**: Fix with `sudo chown -R $(whoami) ~/.npm`

## Development

### Adding New Document Types

Edit `backend/document_processor.py` to add support for new file types.

### Customizing Chunking

Modify chunk size and overlap in `DocumentProcessor.__init__()`.

### Adding New Embedding Models

Extend `EmbeddingProvider` class in `backend/embeddings.py`.

## License

MIT License - See LICENSE file for details