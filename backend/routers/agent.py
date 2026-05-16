from fastapi import APIRouter
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    sessionId: str = Field(..., description="会话 ID，首次传 'new'")
    message: str = Field(..., description="用户消息")
    stream: bool = Field(True, description="是否流式返回，默认 true")


router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/chat")
async def chat(body: ChatRequest):
    return {
        "code": 200,
        "message": "success",
        "data": {
            "sessionId": "sess_abc123",
            "reply": "根据您的食材，推荐西红柿炒鸡蛋...",
            "recipeSource": "rag",
        },
    }


@router.delete("/clear/{session_id}")
async def clear_session(session_id: str):
    return {"code": 200, "message": "会话已清除", "data": None}
