# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

SmartChef — AI 智能厨房助手。拍照识食材 → ChromaDB 菜谱检索 → LangGraph Agent 对话推荐菜品和烹饪指导。统一通过 `/api/agent/chat` SSE 流式交互。

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + LangChain/LangGraph |
| LLM | MIMO API (`mimo-v2.5`) |
| 视觉 | Ollama `qwen3-vl:4b` |
| 向量库 | ChromaDB + `text2vec-base-chinese` |
| 搜索 | Tavily Search API |
| 前端 | Vue 3 + Vite + Pinia |

## Bug 修复工作流

修 Bug 时遵循以下流程：

1. **先定位根因，不要直接改代码。** 追踪完整调用链路，用实际数据复现问题，确认每一个环节的行为。
2. **提出修改方案，征得同意后再动手。** 方案要说明根因和修改点。
3. **改动要小，在原有代码基础上微调。** 不要为了修一个 Bug 引入新抽象、新文件、新工具函数。优先改一两行而不是加几十行。

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

### ChromaDB 相似度分数异常

**现象 1（已修复）：** `UserWarning: Relevance scores must be between 0 and 1, got [...]` 且所有查询都回退到网络搜索。

**根因：** ChromaDB 默认使用 L2 距离，未归一化嵌入向量导致 L2 距离值高达上百，LangChain 的 `_euclidean_relevance_score_fn` 换算后分数为极端负数。

**解决：** `vector_store.py` 中配置 `collection_metadata={"hnsw:space": "cosine"}` 并设置 `encode_kwargs={"normalize_embeddings": True}`。**需要删除旧 `chroma_db/` 后重新入库**（否则 collection 仍使用旧的 L2 索引）。

**当前阈值：** `rag_service.py` 中 `LOCAL_RELEVANCE_THRESHOLD = 0.52`，低于此分数的 chunk 被丢弃。另有菜谱结构校验（chunk 必须包含 `食材清单` 或 `烹饪步骤`），过滤食材搭配指南等非菜谱内容。

### 本地知识库来源误标（LLM 编造菜谱但标注"本地知识库"）

**现象：** 用户上传三文鱼、牛排等食材图片，AI 推荐了清蒸三文鱼、柠檬牛排等菜谱，但来源显示"本地知识库"——而本地菜谱库根本没有三文鱼和牛排相关菜谱。

**根因：** 链路有三层，逐层定位：
1. ChromaDB 语义搜索返回的 top-3 chunk 语义相近但内容无关（如食材搭配指南 0.66、拍黄瓜 0.64、冬瓜排骨汤 0.59）——因为烹饪域内容在嵌入空间中天然接近。
2. 旧版 `retrieve_context` 只要 chunk 通过阈值 + bigram 校验就标记 `【数据来源：本地知识库】`，搭配指南等非菜谱内容侥幸通过。
3. LLM 看到 marker 后信任本地库已命中，忽略实际 chunk 内容，用自身训练数据编造"清蒸三文鱼"等推荐。
4. Source tracker 检测到 marker → 标为"本地知识库"。

**解决（三层防线）：**
| 层 | 位置 | 机制 |
|----|------|------|
| ① 菜谱结构校验 | `rag_service.py` | chunk 必须包含 `食材清单` 或 `烹饪步骤`，过滤搭配指南/去腥技巧等 |
| ② LLM 食材交叉验证 | `agent_service.py` 系统提示 | LLM 看到 marker 后必须先检查返回菜谱是否包含用户核心食材，不包含则必须调 web_search |
| ③ Source tracker 覆盖 | `routers/agent.py` | `web_search` 可覆盖 `retrieve_context` 的 source 标记（去掉 `final_source is None` 条件） |

**验证方法：** 直接调用 `retrieve_context.invoke({'query': '三文鱼 牛排 柠檬 菜谱', 'k': 3})`，确认返回"本地知识库中未找到"而非 marker。


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
  rag.py             # GET /api/rag/status (RAG search happens in-process via agent tools, not via HTTP route)
services/
  __init__.py        # Re-exports all service functions
  agent_service.py   # Agent via langchain.agents.create_agent(), InMemoryStore for long-term memory
                     #   — includes monkey-patch for MIMO API reasoning_content preservation (see below)
                     #   — dual-mode system prompt: mode A (ingredients → recommend/rank), mode B (specific dish → direct recipe)
  rag_service.py     # Recipe ingestion → chunking → ChromaDB; retrieve_context tool with 0.52 relevance threshold, recipe-structure check, source marker + scores
  search_service.py  # Tavily web search (@tool-decorated StructuredTool, exposed as direct agent tool)
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
6. Agent has two tools: `retrieve_context` (local ChromaDB search) and `web_search` (Tavily). `retrieve_context` internally filters chunks by: ① cosine score >= 0.52, ② must contain recipe structure (`食材清单` or `烹饪步骤` — filters out ingredient pairing guides, deodorizing tips, etc.). If verified chunks exist → returns `【数据来源：本地知识库】` + chunks with scores. If not → returns "本地知识库中未找到" with best score vs threshold. System prompt then requires the LLM to cross-check: do the retrieved recipes actually contain the user's core ingredients? If not → must call web_search.
7. Response streams via SSE: `{"sessionId": "..."}` first, then optional `{"status": "..."}`, then `{"token": "..."}` chunks, then programmatic `📎 数据来源：xxx` footer token (if a source was detected), then `[DONE]`
8. Source tracking: router inspects tool output content in `on_tool_end` events. `retrieve_context` → checks for `【数据来源：本地知识库】` in output (only sets if `final_source` is None). `web_search` → checks output doesn't contain "未找到相关搜索结果" (always overrides, because if LLM needed web_search, local results were insufficient). Appends `📎 数据来源：xxx` footer after streaming.

**Session management:** Agents cached in an in-memory `_agents: dict` keyed by session ID. `InMemoryStore` provides cross-session long-term memory for user preferences. Sessions lost on restart.

**MIMO reasoning_content patch** (`agent_service.py` lines 16-35): The MIMO API's thinking mode returns `reasoning_content` in streaming deltas that must be passed back on subsequent conversation turns. `langchain-openai` discards this field entirely. Two module-level monkey-patches fix this:
- `_patched_convert_delta` — captures `reasoning_content` from API deltas into `AIMessageChunk.additional_kwargs`
- `_patched_convert_message` — writes `reasoning_content` back from `AIMessage.additional_kwargs` to the outgoing API request dict

**Vision service** (`services/vision_service.py`): `recognize_ingredients(image_bytes) → list[str]` — base64-encodes image, POSTs to `http://localhost:11434/api/chat` with `qwen3-vl:4b` (timeout=240s), parses JSON ingredient list from response (with regex fallback for malformed output). Runs inside the SSE stream (not as blocking pre-processing); router catches exceptions and degrades gracefully — the conversation continues even if vision fails.

**RAG pipeline** (`services/rag_service.py`): recipes loaded with `TextLoader(encoding="utf-8")` (GBK default on Windows breaks CJK characters) → chunked via `RecursiveCharacterTextSplitter` (chunk_size=500, overlap=50) → ChromaDB (cosine distance, `normalize_embeddings=True`). `retrieve_context` uses `similarity_search_with_relevance_scores` with `LOCAL_RELEVANCE_THRESHOLD = 0.52` — chunks below threshold are discarded. Verified chunks must also contain `食材清单` or `烹饪步骤` to filter out non-recipe content (ingredient pairing guides, deodorizing tips). Match returns `【数据来源：本地知识库】` with per-chunk scores; no match or no verified chunks → returns best score vs threshold so the LLM can decide. System prompt additionally requires the LLM to verify retrieved recipes contain the user's ingredients before using them — if not, it must call web_search.

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

**State** lives in Pinia `chat` store: `sessions`, `activeSessionId`, `pendingImage`, `isStreaming`, `ragTotalChunks`. No frontend-side recipe matching or ingredient logic.

### Key external services

| Service | Purpose | Model/Provider |
|---------|---------|----------------|
| MIMO API | LLM (agent conversations) | `mimo-v2.5` via OpenAI-compatible endpoint |
| Ollama | On-device vision (ingredient recognition) | `qwen3-vl:4b` on `localhost:11434` |
| ChromaDB | Recipe vector store (local persistence) | `shibing624/text2vec-base-chinese` embeddings |
| Tavily | Web search fallback for recipes | — |

### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/agent/chat` | FormData: `sessionId`, `message` (optional), `file` (optional image). Returns SSE stream. |
| DELETE | `/api/agent/clear/{sessionId}` | Clear agent session from memory. |
| GET | `/api/rag/status` | ChromaDB chunk count. |
| GET | `/api/rag/search?query=&k=` | (commented out — unused, agent calls retrieve_context in-process instead) |

### Environment variables (.env at project root)

| Variable | Required | Default | Usage |
|----------|----------|---------|-------|
| `MIMO_API_KEY` | Yes | — | LLM API key |
| `MIMO_BASE_URL` | No | `https://api.xiaomimimo.com/v1` | LLM endpoint |
| `TAVILY_API_KEY` | Yes | — | Web search fallback |
| `LANGSMITH_API_KEY` | No | — | LangSmith tracing |
| `EMBEDDING_MODEL_NAME` | No | `shibing624/text2vec-base-chinese` | HuggingFace embedding model |

`.env` also contains `DEEPSEEK_API_KEY`, `JINA_API_KEY`, `DASHSCOPE_API_KEY`, `MINMAX_API_KEY` which are declared but not used by current code.
