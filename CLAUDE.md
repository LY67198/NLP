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

## Troubleshooting

### Ollama GPU 未启用（CPU-only 导致超时）

**现象：** `httpx.ReadTimeout` 从 vision_service 抛出，Ollama `/api/chat` 请求耗时 2-4 分钟返回 500。

**诊断：**
```bash
ollama ps          # 查看 PROCESSOR 列：100% CPU = GPU 未启用
ollama logs        # 查看是否有 "failure during GPU discovery" / "offloaded 0/37 layers to GPU"
```

**根因：** Ollama GPU 发现偶发超时失败，回退到纯 CPU 推理。日志标记：`failure during GPU discovery ... timeout`，随后 `inference compute id=cpu ... total_vram="0 B"`。

**解决：** 重启 Ollama（托盘图标退出后重新启动）。重启后日志应显示：`inference compute ... library=CUDA ... total="6.0 GiB"`。

**验证：** `ollama ps` 中 PROCESSOR 应显示为 GPU 百分比（如 `100% GPU`）。

### httpx 超时配置

vision_service.py 中 `httpx.AsyncClient(timeout=240.0)` 控制 Ollama 视觉识别超时。GPU 启用时识别通常 5-15 秒完成；CPU-only 可能需要 2-4 分钟。此 timeout 已在 2026-05-18 从 60s 调整为 240s 以兼容 CPU fallback 场景。

### ChromaDB 相似度分数异常（全部为负数）

**现象：** `UserWarning: Relevance scores must be between 0 and 1, got [...]` 且所有查询都回退到网络搜索（不论本地库是否有匹配菜谱）。

**根因：** ChromaDB 默认使用 L2 距离，`shibing624/text2vec-base-chinese` 输出的未归一化嵌入向量导致 L2 距离值高达上百，LangChain 的 `_euclidean_relevance_score_fn` 换算后分数为极端负数，`RELEVANCE_THRESHOLD = 0.4` 永远不命中。

**解决：** `vector_store.py` 中配置 `collection_metadata={"hnsw:space": "cosine"}` 并设置 `encode_kwargs={"normalize_embeddings": True}`。**需要删除旧 `chroma_db/` 后重新入库**（否则 collection 仍使用旧的 L2 索引）。`main.py` 的 `lifespan` 事件会在启动时自动检测空库并调用 `ingest_file()`。

### Windows 下 TextLoader 编码报错

**现象：** `UnicodeDecodeError: 'gbk' codec can't decode byte 0xae`

**根因：** `TextLoader` 在 Windows 上默认使用系统编码（GBK），而 `recipes_dataset.txt` 是 UTF-8 编码。

**解决：** `TextLoader(file_path, encoding="utf-8")`。

## Architecture

SmartChef is an AI-powered kitchen assistant: upload a photo of ingredients → vision model identifies them → RAG retrieves matching recipes → conversational agent recommends dishes and guides cooking. All interaction goes through a single `/api/agent/chat` SSE streaming endpoint.

### Backend (FastAPI on :8000)

```
main.py              # App entry: CORS, lifespan (auto-ingest recipes if empty), includes agent + rag routers
routers/
  __init__.py        # Empty
  agent.py           # POST /api/agent/chat (SSE stream, FormData: sessionId + message + optional file)
                     #   — sessionId="new" generates UUID; file triggers vision pre-processing inline
                     #   — source tracking: extracts .content from ToolMessage (not raw str) in on_tool_end events
                     # DELETE /api/agent/clear/{session_id}
  rag.py             # GET /api/rag/status, GET /api/rag/search
services/
  __init__.py        # Re-exports all service functions
  agent_service.py   # Agent via langchain.agents.create_agent(), InMemoryStore for long-term memory
                     #   — includes monkey-patch for MIMO API reasoning_content preservation (see below)
                     #   — dual-mode system prompt: mode A (ingredients → recommend/rank), mode B (specific dish → direct recipe)
  rag_service.py     # Recipe ingestion → chunking → ChromaDB; retrieve_context tool (local-first, auto-fallback to web_search)
  search_service.py  # Tavily web search (@tool-decorated StructuredTool, called via .invoke() not direct call)
  vision_service.py  # Ollama qwen3-vl:4b ingredient recognition via httpx
  vector_store.py    # ChromaDB singleton, HuggingFace text2vec-base-chinese embeddings with normalize_embeddings=True, cosine distance
utils/
  __init__.py        # Empty
  response.py        # JSON response helper
data/
  recipes/
    recipes_dataset.txt  # Default recipe corpus for RAG ingestion (UTF-8 encoded)
  chroma_db/             # ChromaDB persistent storage (cosine distance)
```

**Agent flow** (`routers/agent.py` → `services/agent_service.py`):
1. Request arrives with `sessionId`, `message`, optional `file`
2. If `sessionId == "new"` → generates UUID. If `file` present → reads image bytes early (before SSE stream)
3. SSE stream starts **immediately**: first event `{"sessionId": "..."}` so frontend always gets a response
4. If image present → `{"status": "正在分析图片中的食材..."}` event, then `vision_service.recognize_ingredients()` runs **inside** the stream. On success → ingredient list injected as message prefix. On failure → error status event, flow continues with original message (graceful degradation)
5. `get_or_create_agent(session_id)` returns cached or new agent via `create_agent(model, tools, system_prompt=...)`
6. Agent has a single tool `retrieve_context`, which internally handles both ChromaDB RAG and Tavily web search fallback
7. Response streams via SSE: `{"sessionId": "..."}` first, then optional `{"status": "..."}`, then `{"token": "..."}` chunks, then programmatic `📎 数据来源：xxx` footer token (if retrieve_context was called), then `[DONE]`
8. Source tracking: router listens for `on_tool_end` events from `retrieve_context`. LangGraph wraps tool output in `ToolMessage` objects — the router extracts `.content` (not the raw `output` string) to detect `【数据来源：本地知识库】` or `【数据来源：网络搜索】` labels, collecting unique sources in a set, and appending a `📎 数据来源：xxx` footer token after the model finishes streaming. This is programmatic — does not rely on the model preserving labels in its response.

**Session management:** Agents cached in an in-memory `_agents: dict` keyed by session ID. `InMemoryStore` provides cross-session long-term memory for user preferences. Sessions lost on restart.

**MIMO reasoning_content patch** (`agent_service.py` lines 16-35): The MIMO API's thinking mode returns `reasoning_content` in streaming deltas that must be passed back on subsequent conversation turns. `langchain-openai` discards this field entirely. Two module-level monkey-patches fix this:
- `_patched_convert_delta` — captures `reasoning_content` from API deltas into `AIMessageChunk.additional_kwargs`
- `_patched_convert_message` — writes `reasoning_content` back from `AIMessage.additional_kwargs` to the outgoing API request dict

**Vision service** (`services/vision_service.py`): `recognize_ingredients(image_bytes) → list[str]` — base64-encodes image, POSTs to `http://localhost:11434/api/chat` with `qwen3-vl:4b` (timeout=240s), parses JSON ingredient list from response (with regex fallback for malformed output). Runs inside the SSE stream (not as blocking pre-processing); router catches exceptions and degrades gracefully — the conversation continues even if vision fails.

**RAG pipeline** (`services/rag_service.py`): recipes loaded with `TextLoader(encoding="utf-8")` (GBK default on Windows breaks CJK characters) → chunked via `RecursiveCharacterTextSplitter` (chunk_size=500, overlap=50) → ChromaDB (cosine distance, `normalize_embeddings=True`). `retrieve_context` tool uses `similarity_search_with_relevance_scores` with a relevance threshold (0.4 on 0-1 scale) — low-quality matches are filtered out, triggering web search fallback. Results prefixed with `【数据来源：本地知识库】` or `【数据来源：网络搜索】`, parsed by router to programmatically append a source footer. Note: `web_search` is a `@tool`-decorated `StructuredTool` and must be called via `.invoke({"query": query})`, not as a plain function.

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
    MessageBubble.vue  # Single chat message rendering (text, images, ingredient tags, sources). Parses 【数据来源：...】 from AI response → renders source badges (green=local, blue=web)
    WelcomeCard.vue    # Empty-state prompt suggestions (3 example prompts)
    ImagePreview.vue   # Thumbnail of pending upload with remove button
    IngredientTags.vue # Editable ingredient chips (defined but not wired in current render flow)
    RecipeCards.vue    # Structured recipe cards from agent responses (defined but not wired)
  styles/
    main.css           # Global styles, low-saturation warm palette
```

**Data flow:** User types text / uploads image / both → `chat.js:sendMessage()` → POST `/api/agent/chat` with FormData (sessionId, message, file) → SSE stream: `sessionId` event first, optional `status` events (e.g. "正在分析图片中的食材..."), then `token` chunks streamed in real time. Status text is shown in the AI message bubble and replaced by the first real token (avoids "dirty" concatenation).

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
