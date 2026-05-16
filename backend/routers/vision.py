from fastapi import APIRouter, File, Form, UploadFile

router = APIRouter(prefix="/api/vision", tags=["vision"])


@router.post("/recognize")
async def recognize_ingredients(
    file: UploadFile = File(..., description="图片，支持 jpg / png / webp，≤10MB"),
):
    return {
        "code": 200,
        "message": "识别成功",
        "data": {
            "rawDescription": "图片中包含：鸡蛋（约6个）、西红柿（2个）、土豆（3个）",
            "ingredients": ["鸡蛋", "西红柿", "土豆"],
            "confidence": "high",
        },
    }


@router.post("/chat")
async def vision_chat(
    file: UploadFile = File(..., description="图片文件"),
    sessionId: str = Form(..., description="会话 ID，首次传 'new'"),
    message: str = Form("", description="用户附带文字，可为空"),
    stream: bool = Form(False, description="是否流式返回，默认 false"),
):
    return {
        "code": 200,
        "message": "success",
        "data": {
            "sessionId": "sess_abc123",
            "recognizedIngredients": ["鸡蛋", "西红柿", "土豆"],
            "reply": "根据识别到的食材，推荐以下菜品...",
            "recipeSource": "rag",
        },
    }
