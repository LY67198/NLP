"""
GPT-4o Vision 多模态识图服务。
上传食材/冰箱照片，识别图片中的食材并返回结构化列表。
"""

from typing import TypedDict


class VisionResult(TypedDict):
    """识图返回结构。"""
    rawDescription: str          # 自然语言描述，如 "图片中包含：鸡蛋（约6个）、西红柿（2个）"
    ingredients: list[str]       # 识别到的食材名称列表
    confidence: str              # 置信度，取值为 "high" / "medium" / "low"


def recognize_ingredients(image_bytes: bytes) -> VisionResult:
    """识别图片中的食材。

    Args:
        image_bytes: 图片文件的原始字节数据，支持 jpg / png / webp 格式。

    Returns:
        VisionResult: 包含自然语言描述、食材列表和置信度的结构化结果。
    """


def recognize_ingredients_b64(image_b64: str) -> VisionResult:
    """识别 Base64 编码图片中的食材（用于前端直接传 base64 的场景）。

    Args:
        image_b64: 图片的 Base64 编码字符串（不含 data:xxx;base64, 前缀）。

    Returns:
        VisionResult: 同 recognize_ingredients。
    """
