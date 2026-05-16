# Smart Chef — 开发计划

> 状态快照 (2026-05-16)：RAG 管线（ChromaDB + 语义检索 + Tavily 联网搜索）及 Streamlit 前端 UI 已基本完成。Agent 服务、Vision 服务、LLM 集成尚未启动，对应路由返回硬编码 mock 数据。

---

## 阶段一：打通 LLM 调用链路

**目标**：让 Agent 能真正"对话"，替代当前 mock 响应。

| # | 任务 | 涉及文件 | 说明 |
|---|------|---------|------|
| 1.1 | 封装 LLM 调用 | 新建 `backend/services/llm_service.py` | 统一封装 DeepSeek / MIMO 等 API 调用，暴露 `chat(messages, tools?)` 接口，其他模块不直接调 openai SDK |
| 1.2 | 实现 Agent Service | `backend/services/agent_service.py` | 构建 LangGraph `StateGraph`：节点包含 `call_model` → `route_tools` → `call_tools` → 回到 `call_model`；工具列表注入 `retrieve_context` + `web_search`；每 session 缓存一个 `CompiledGraph` 实例 |
| 1.3 | 接入 Agent Router | `backend/routers/agent.py` | 替换 mock 响应，调用 `get_or_create_agent(session_id).astream()` 实现真正的 SSE 流式输出；处理流式 chunk 格式与前端对齐 |
| 1.4 | 实现 session 清理 | `backend/services/agent_service.py` / `backend/routers/agent.py` | `clear_session()` 清理图实例 + InMemoryStore 中的对话历史 |

**验收标准**：前端发起文本对话，Agent 能调用 RAG 检索菜谱并流式返回结果；RAG 无结果时自动切换到 web_search。

---

## 阶段二：实现 Vision 食材识别

**目标**：照片识食材，"拍照出菜谱"链路跑通。

| # | 任务 | 涉及文件 | 说明 |
|---|------|---------|------|
| 2.1 | 实现 Vision Service | `backend/services/vision_service.py` | 调用 GPT-4o / DeepSeek-VL 等多模态模型，传入图片 bytes，prompt 约束输出为 JSON 食材列表 |
| 2.2 | 接入 Vision Router | `backend/routers/vision.py` | 替换 mock 响应，`recognize` 返回识别食材清单，`chat` 将识别结果注入 Agent 对话上下文 |
| 2.3 | 优化识别 prompt | `backend/services/vision_service.py` | 限制中餐常见食材，排除非食材物体，输出格式稳定为 `["食材1", "食材2"]` |

**验收标准**：上传一张食材照片 → 正确识别出食材 → 自动带入 Agent 对话 → Agent 基于食材推荐菜谱。

---

## 阶段三：完善 RAG 路由

**目标**：补全文档入库接口，支持通过 API 动态扩展知识库。

| # | 任务 | 涉及文件 | 说明 |
|---|------|---------|------|
| 3.1 | 实现 ingest 接口 | `backend/routers/rag.py` | 接收文件上传 → 保存临时文件 → 调用 `rag_service.ingest_file(path)` → 返回入库 chunk 数量 |
| 3.2 | 增加错误处理 | `backend/routers/rag.py` | 文件格式校验、大小限制、重复入库去重提示 |
| 3.3 | 前端接入 | `frontend/app.py` / `frontend/api_client.py` | 管理面板或侧边栏添加上传菜谱入口 |

**验收标准**：通过 API 上传新的 `.txt` / `.md` 菜谱文件，ChromaDB 增量入库，前端即时体现。

---

## 阶段四：前端增强与用户体验

**目标**：打磨交互细节，让产品可日常使用。

| # | 任务 | 说明 |
|---|------|------|
| 4.1 | 消息内展示菜谱卡片 | 解析 Agent 返回的菜谱结构化内容，渲染为独立卡片（名称、食材、步骤、时间、难度）而非纯文本 |
| 4.2 | 图片上传流程优化 | 上传后显示缩略图预览 + 识别进度，识别结果可编辑修正后再发起对话 |
| 4.3 | 对话历史持久化 | 用 `st.session_state` 导出/导入或对接轻量数据库（SQLite），刷新不丢失 |
| 4.4 | 错误 & 空状态优化 | API 调用失败的友好提示、网络超时重试、空检索结果的引导话术 |
| 4.5 | 移动端适配 | Streamlit 响应式布局调整，确保手机端可用 |

---

## 阶段五：生产化

**目标**：从 demo 升级为可部署的服务。

| # | 任务 | 说明 |
|---|------|------|
| 5.1 | 配置管理 | 统一从 `.env` 读取，启动时校验必须的 API key，缺失时报错退出 |
| 5.2 | 日志系统 | 结构化日志记录（请求 ID、耗时、工具调用链），便于排查问题 |
| 5.3 | Docker 化 | 编写 `Dockerfile` + `docker-compose.yml`（FastAPI + Streamlit 双容器） |
| 5.4 | 测试 | 核心模块单测：`rag_service`、`search_service`、`vector_store`；Agent 集成测试 |
| 5.5 | README | 项目说明、本地启动步骤、环境变量配置说明、API 文档链接 |

---

## 优先级排序

```
阶段一（LLM 链路）  ████████████████  最高 — 无此则核心能力不可用
阶段二（Vision）    ████████████      高   — 核心差异功能
阶段三（RAG 路由）  ████████          中   — 当前可手动补数据，阻塞不强
阶段四（UX）        ██████            中低 — 不影响功能，提升体验
阶段五（生产化）    ████              低   — 部署前再做
```

## 技术选型建议

| 决策点 | 建议 | 理由 |
|--------|------|------|
| LLM 模型 | DeepSeek-V3（已有 key）或 MIMO | 成本低、中文能力强、支持 function calling |
| Agent 框架 | LangGraph `create_react_agent` | 已在依赖中，创建 ReAct agent 只需 5 行代码 |
| Vision 模型 | GPT-4o 或 DeepSeek-VL | 食材识别不需要最强模型，DeepSeek-VL 够用且便宜 |
| 对话记忆 | LangGraph `InMemoryStore` | 已在 agent_service 注释中规划，按 user_id 持久化偏好 |
| 流式响应 | FastAPI SSE (`StreamingResponse`) | 已有部分基础设施在 agent router 中 |

---

## 阶段一实现要点

以下是阶段一最核心的代码结构参考，供开工时对齐：

### 1.1 LLM 调用封装

```python
# backend/services/llm_service.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

def get_llm(model: str = "deepseek-chat") -> ChatOpenAI:
    """返回绑定了工具调用能力的 LLM 实例。"""
    return ChatOpenAI(
        model=model,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com/v1",
        temperature=0.7,
    )
```

### 1.2 Agent 构建（LangGraph ReAct 模式）

```python
# backend/services/agent_service.py（替换原有 stub）
from langgraph.prebuilt import create_react_agent
from services.rag_service import retrieve_context
from services.search_service import web_search
from services.llm_service import get_llm

_agents: dict[str, CompiledStateGraph] = {}

def get_or_create_agent(session_id: str):
    if session_id not in _agents:
        llm = get_llm()
        tools = [retrieve_context, web_search]
        _agents[session_id] = create_react_agent(llm, tools)
    return _agents[session_id]
```

### 1.3 Router 流式对接

```python
# backend/routers/agent.py（替换 mock）
@router.post("/chat")
async def agent_chat(req: ChatRequest):
    agent = get_or_create_agent(req.sessionId)

    async def event_stream():
        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": req.message}]},
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield f"data: {chunk.content}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```
