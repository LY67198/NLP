# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development commands

```bash
# Environment setup (UV)
uv venv --python cpython-3.13
uv pip install -r requirements.txt

# Activate virtual environment (Windows)
.venv/Scripts/activate

# Backend (from backend/)
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (from frontend-vue/)
npm run dev       # Vite dev server on :3000, proxies /api → :8000
npm run build     # production build

# One-click launch (Windows)
start.bat         # starts Ollama check → backend → frontend → opens browser
```

**Prerequisites:** Ollama running locally with `qwen3-vl:4b` model pulled on port 11434. Backend requires a `.env` file at project root with `MIMO_API_KEY`, `TAVILY_API_KEY`. `MIMO_BASE_URL` defaults to `https://api.xiaomimimo.com/v1` if not set.

No test suite is configured yet.

## Architecture

SmartChef is an AI-powered kitchen assistant: upload a photo of ingredients → vision model identifies them → RAG retrieves matching recipes → conversational agent recommends dishes and guides cooking. All interaction goes through a single `/api/agent/chat` SSE streaming endpoint.

### Backend (FastAPI on :8000)

```
main.py              # App entry: CORS, / health check, includes agent + rag routers
routers/
  __init__.py        # Empty
  agent.py           # POST /api/agent/chat (SSE stream, FormData: sessionId + message + optional file)
                     #   — sessionId="new" generates UUID; file triggers vision pre-processing inline
                     # DELETE /api/agent/clear/{session_id}
  rag.py             # GET /api/rag/status, GET /api/rag/search
services/
  __init__.py        # Re-exports all service functions
  agent_service.py   # Agent via langchain.agents.create_agent(), InMemoryStore for long-term memory
                     #   — includes monkey-patch for MIMO API reasoning_content preservation (see below)
  rag_service.py     # Recipe ingestion → chunking → ChromaDB; retrieve_context tool
  search_service.py  # Tavily web search tool (fallback when local RAG misses)
  vision_service.py  # Ollama qwen3-vl:4b ingredient recognition via httpx
  vector_store.py    # ChromaDB singleton, HuggingFace text2vec-base-chinese embeddings
utils/
  __init__.py        # Empty
  response.py        # JSON response helper
data/
  recipes/
    recipes_dataset.txt  # Default recipe corpus for RAG ingestion
  chroma_db/             # ChromaDB persistent storage
```

**Agent flow** (`routers/agent.py` → `services/agent_service.py`):
1. Request arrives with `sessionId`, `message`, optional `file`
2. If `sessionId == "new"` → generates UUID. If `file` present → `vision_service.recognize_ingredients()` calls Ollama qwen3-vl:4b → ingredient list injected as message prefix
3. `get_or_create_agent(session_id)` returns cached or new agent via `create_agent(model, tools, system_prompt=...)`
4. Agent has two tools: `retrieve_context` (ChromaDB RAG) and `web_search` (Tavily)
5. Response streams via SSE: `{"sessionId": "..."}` first, then `{"token": "..."}` chunks, then `[DONE]`

**Session management:** Agents cached in an in-memory `_agents: dict` keyed by session ID. `InMemoryStore` provides cross-session long-term memory for user preferences. Sessions lost on restart.

**MIMO reasoning_content patch** (`agent_service.py` lines 16-35): The MIMO API's thinking mode returns `reasoning_content` in streaming deltas that must be passed back on subsequent conversation turns. `langchain-openai` discards this field entirely. Two module-level monkey-patches fix this:
- `_patched_convert_delta` — captures `reasoning_content` from API deltas into `AIMessageChunk.additional_kwargs`
- `_patched_convert_message` — writes `reasoning_content` back from `AIMessage.additional_kwargs` to the outgoing API request dict

**Vision service** (`services/vision_service.py`): `recognize_ingredients(image_bytes) → list[str]` — base64-encodes image, POSTs to `http://localhost:11434/api/chat` with `qwen3-vl:4b`, parses JSON ingredient list from response (with regex fallback for malformed output). Runs as preprocessing before the agent, not as an agent tool.

**RAG pipeline** (`services/rag_service.py`): recipes split on `\n---\n` → chunks via `RecursiveCharacterTextSplitter` (chunk_size=500, overlap=50) → ChromaDB. `retrieve_context` tool prefers local RAG, falls back to `web_search`.

### Frontend (Vue 3 + Vite on :3000)

```
src/
  main.js              # App entry, Pinia setup
  App.vue              # Layout: Sidebar + ChatArea
  api/client.js        # SSE stream reader + agentChatStream (FormData with optional file)
  stores/chat.js       # Pinia store: session CRUD, unified sendMessage (text/image/image+text)
  components/
    ChatArea.vue       # Message list, streaming indicator, delegates to ChatInput
    Sidebar.vue        # Session list sidebar, RAG status display
    ChatInput.vue      # Text input + image upload button, Enter to send
    MessageBubble.vue  # Single chat message rendering (text, images, ingredient tags, sources)
    WelcomeCard.vue    # Empty-state prompt suggestions (3 example prompts)
    ImagePreview.vue   # Thumbnail of pending upload with remove button
    IngredientTags.vue # Editable ingredient chips (defined but not wired in current render flow)
    RecipeCards.vue    # Structured recipe cards from agent responses (defined but not wired)
  styles/
    main.css           # Global styles, low-saturation warm palette
```

**Data flow:** User types text / uploads image / both → `chat.js:sendMessage()` → POST `/api/agent/chat` with FormData (sessionId, message, file) → SSE streamed tokens appended to last AI message in real time.

**State** lives in Pinia `chat` store: `sessions`, `activeSessionId`, `pendingImage`, `isStreaming`. No frontend-side recipe matching or ingredient logic.

### Key external services

| Service | Purpose | Model/Provider |
|---------|---------|----------------|
| MIMO API | LLM (agent conversations) | `mimo-v2-omni` via OpenAI-compatible endpoint |
| Ollama | On-device vision (ingredient recognition) | `qwen3-vl:4b` on `localhost:11434` |
| ChromaDB | Recipe vector store (local persistence) | `shibing624/text2vec-base-chinese` embeddings |
| Tavily | Web search fallback for recipes | — |

### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/agent/chat` | FormData: `sessionId`, `message` (optional), `file` (optional image). Returns SSE stream. |
| DELETE | `/api/agent/clear/{sessionId}` | Clear agent session from memory. |
| GET | `/api/rag/status` | ChromaDB chunk count. |
| GET | `/api/rag/search?query=&k=` | Semantic recipe search. |

### Environment variables (.env at project root)

| Variable | Required | Default | Usage |
|----------|----------|---------|-------|
| `MIMO_API_KEY` | Yes | — | LLM API key |
| `MIMO_BASE_URL` | No | `https://api.xiaomimimo.com/v1` | LLM endpoint |
| `TAVILY_API_KEY` | Yes | — | Web search fallback |
| `LANGSMITH_API_KEY` | No | — | LangSmith tracing |
| `EMBEDDING_MODEL_NAME` | No | `shibing624/text2vec-base-chinese` | HuggingFace embedding model |

`.env` also contains `DEEPSEEK_API_KEY`, `JINA_API_KEY`, `DASHSCOPE_API_KEY`, `MINMAX_API_KEY` which are declared but not used by current code.
