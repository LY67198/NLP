import json
import uuid
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from services import agent_service
from services.vision_service import recognize_ingredients

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/chat")
async def chat(
    sessionId: str = Form(...),
    message: str = Form(""),
    file: UploadFile | None = File(None),
):
    if sessionId == "new":
        sessionId = str(uuid.uuid4())

    # 提前读取图片字节，避免阻塞 SSE 流的启动
    img_bytes = None
    if file is not None:
        img_bytes = await file.read()

    async def event_stream():
        # 立即发送 sessionId，让前端知道连接已建立
        yield f"data: {json.dumps({'sessionId': sessionId})}\n\n"

        nonlocal message

        # 图片预处理：在 SSE 流内进行，发送状态通知前端
        if img_bytes is not None:
            yield f"data: {json.dumps({'status': '正在分析图片中的食材...'})}\n\n"
            try:
                ingredients = await recognize_ingredients(img_bytes)
                prefix = f"用户上传了一张食材图片，识别到以下食材：{', '.join(ingredients)}。"
                message = f"{prefix} {message or '请根据这些食材推荐菜谱。'}"
            except Exception as e:
                yield f"data: {json.dumps({'status': f'图片识别失败，将直接处理您的消息。'})}\n\n"
                # 继续使用原始消息，不阻断流程

        agent = agent_service.get_or_create_agent(sessionId)

        final_source = None  # 来源追踪：记录最终用于回答的来源

        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": message}]},
            version="v2",
        ):
            # 追踪工具调用来源：只有工具返回有效结果才标记来源
            if event["event"] == "on_tool_end":
                tool_name = event.get("name", "")
                raw = event.get("data", {}).get("output", "")
                # ToolMessage 对象取 .content，字符串直接用
                output = getattr(raw, "content", raw) if hasattr(raw, "content") else raw
                output = str(output)
                if tool_name == "retrieve_context":
                    if final_source is None and "【数据来源：本地知识库】" in output:
                        final_source = "本地知识库"
                elif tool_name == "web_search" and "未找到相关搜索结果" not in output:
                    final_source = "网络搜索"

            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield f"data: {json.dumps({'token': chunk.content})}\n\n"

        # 流结束后追加来源脚注
        if final_source:
            yield f"data: {json.dumps({'token': f'\\n\\n📎 数据来源：{final_source}'})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.delete("/clear/{session_id}")
async def clear_session(session_id: str):
    ok = agent_service.clear_session(session_id)
    return {"code": 200 if ok else 404, "message": "已清除" if ok else "会话不存在", "data": None}
