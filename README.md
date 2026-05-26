# SmartChef — AI 智能厨房助手

拍一张食材照片，SmartChef 就能识别出有什么食材，从本地菜谱库中检索匹配的菜谱，并通过对话为你推荐菜品、指导烹饪步骤。

## 功能特性

- **拍照识食材** — 上传食材照片，本地 Ollama 视觉模型自动识别食材清单
- **智能菜谱推荐** — 基于 ChromaDB 向量检索，从本地菜谱库中匹配最佳菜谱
- **网络搜索兜底** — 本地菜谱库未覆盖时，自动通过 Tavily 联网搜索补充
- **多轮对话指导** — 支持追问替代食材、调整做法、细化步骤，像和真人厨师聊天一样
- **流式实时回复** — 基于 SSE 的流式输出，无需等待完整回复

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| AI Agent | LangChain + LangGraph |
| LLM | MIMO API (`mimo-v2-omni`) |
| 视觉识别 | Ollama (`qwen3-vl:4b`) |
| 向量检索 | ChromaDB + HuggingFace (`text2vec-base-chinese`) |
| 网络搜索 | Tavily Search API |
| 前端 | Vue 3 + Vite + Pinia |
| 包管理 | UV (Python) / npm (前端) |

## 快速开始

### 前置条件

1. 安装并启动 [Ollama](https://ollama.com/)，拉取视觉模型：
   ```bash
   ollama pull qwen3-vl:4b
   ```
2. 准备 API Key：
   - `MIMO_API_KEY` — LLM 调用
   - `TAVILY_API_KEY` — 网络搜索兜底

### 一键启动（Windows）

```bash
start.bat
```

脚本会自动完成：检查 Ollama 运行状态 → 启动后端(:8000) → 启动前端(:3000) → 打开浏览器。

### 手动启动

```bash
# 1. 后端
cd backend
uv venv --python cpython-3.13
uv pip install -r requirements.txt
cp .env.example .env   # 编辑填入 API Key
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 2. 前端（新终端）
cd frontend-vue
npm install
npm run dev
```

浏览器访问 `http://localhost:3000`。

## 项目结构

```
smart-chef/
├── backend/
│   ├── main.py                  # 应用入口，CORS、生命周期
│   ├── routers/
│   │   ├── agent.py             # POST /api/agent/chat (SSE) + 会话管理
│   │   └── rag.py               # GET /api/rag/status
│   ├── services/
│   │   ├── agent_service.py     # LangGraph Agent，双模式系统提示
│   │   ├── rag_service.py       # 菜谱入库、分块、检索
│   │   ├── search_service.py    # Tavily 网络搜索
│   │   ├── vision_service.py    # Ollama 视觉识别
│   │   └── vector_store.py      # ChromaDB 单例
│   └── data/
│       ├── recipes/             # 菜谱语料
│       └── chroma_db/           # 向量持久化
├── frontend-vue/
│   └── src/
│       ├── api/client.js        # SSE 流式客户端
│       ├── stores/chat.js       # Pinia 状态管理
│       └── components/          # Vue 组件
├── requirements.txt
└── start.bat
```

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/agent/chat` | 核心对话接口。FormData：`sessionId`、`message`（可选）、`file`（可选图片）。返回 SSE 流。 |
| DELETE | `/api/agent/clear/{sessionId}` | 清除指定会话 |
| GET | `/api/rag/status` | 查看 ChromaDB 中菜谱分块数量 |

## 环境变量

在 `backend/.env` 中配置：

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `MIMO_API_KEY` | 是 | — | LLM API 密钥 |
| `MIMO_BASE_URL` | 否 | `https://api.xiaomimimo.com/v1` | LLM 接口地址 |
| `TAVILY_API_KEY` | 是 | — | Tavily 搜索 API 密钥 |
| `EMBEDDING_MODEL_NAME` | 否 | `shibing624/text2vec-base-chinese` | 嵌入模型 |
| `LANGSMITH_API_KEY` | 否 | — | LangSmith 调试追踪 |

## 注意事项

### Ollama GPU 加速

如遇到视觉识别超时（2-4 分钟），可能是 Ollama 未启用 GPU。运行 `ollama ps` 检查 PROCESSOR 列：显示 `100% GPU` 为正常，`100% CPU` 则需重启 Ollama。

### ChromaDB 相似度

如果菜谱检索结果不相关，删除 `backend/data/chroma_db/` 目录后重启后端，让 ChromaDB 以 cosine 距离重建索引。

### Windows 编码

菜谱数据文件需使用 UTF-8 编码保存，否则中文内容会出现乱码。
