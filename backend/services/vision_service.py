import base64
import json
import re
import httpx

OLLAMA_BASE = "http://localhost:11434"
VISION_MODEL = "qwen3-vl:4b"


async def recognize_ingredients(image_bytes: bytes) -> list[str]:
    """识别图片中的食材，返回食材名称列表。"""
    image_b64 = base64.b64encode(image_bytes).decode()

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{OLLAMA_BASE}/api/chat",
            json={
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": "请识别图片中的所有食材，只返回食材名称的JSON列表，如[\"鸡蛋\",\"西红柿\"]。不要返回其他内容。",
                        "images": [image_b64],
                    }
                ],
                "stream": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "[]")

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\[.*?\]", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return []
