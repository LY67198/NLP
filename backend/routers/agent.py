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

    # 图片预处理：先识图，将食材注入消息
    if file is not None:
        img_bytes = await file.read()
        ingredients = await recognize_ingredients(img_bytes)
        prefix = f"用户上传了一张食材图片，识别到以下食材：{', '.join(ingredients)}。"
        message = f"{prefix} {message or '请根据这些食材推荐菜谱。'}"

    agent = agent_service.get_or_create_agent(sessionId)

    async def event_stream():
        yield f"data: {json.dumps({'sessionId': sessionId})}\n\n"
        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": message}]},
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield f"data: {json.dumps({'token': chunk.content})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.delete("/clear/{session_id}")
async def clear_session(session_id: str):
    ok = agent_service.clear_session(session_id)
    return {"code": 200 if ok else 404, "message": "已清除" if ok else "会话不存在", "data": None}
