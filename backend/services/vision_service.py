"""
qwen3-vl:4b 多模态识图服务。
上传食材/冰箱照片，识别图片中的食材并返回结构化列表。
"""

from typing import Any, Literal
from langchain_ollama import ChatOllama
from pydantic import BaseModel, ConfigDict, Field
import base64
import json
import re

from langchain_core.messages import HumanMessage


# 单字食材白名单 — 模型可能返回的合法单字中文食材名
_SINGLE_CHAR_FOODS = frozenset({
    "葱", "姜", "蒜", "蛋", "虾", "蟹", "鱼",
    "鸡", "鸭", "牛", "羊", "猪",
})


model = ChatOllama(model="qwen3-vl:4b", temperature=0)


class VisionResult(BaseModel):
    """识图返回结构。"""

    model_config = ConfigDict(populate_by_name=True)

    raw_description: str = Field(
        ...,
        validation_alias="rawDescription",
        serialization_alias="rawDescription",
    )
    ingredients: list[str]
    confidence: Literal["high", "medium", "low"]


def _valid_ingredient_length(text: str) -> bool:
    """食材名长度校验：2-12 字直接通过，单字需在白名单中。"""
    if not text:
        return False
    length = len(text)
    if 2 <= length <= 12:
        return True
    if length == 1 and text in _SINGLE_CHAR_FOODS:
        return True
    return False


def _extract_ingredients_from_text(text: str) -> list[str]:
    """从 LLM 返回的非标准文本中尽可能提取食材名称。

    依次尝试：JSON 数组匹配 → 常见中文食材关键词匹配 → 逗号/顿号分割。
    """
    # 尝试匹配 JSON 数组：["食材A", "食材B"]
    json_arr = re.search(r'\[([^\]]*)\]', text)
    if json_arr:
        items = re.findall(r'"([^"]*)"', json_arr.group(1))
        if items:
            return [i.strip() for i in items if _valid_ingredient_length(i.strip())][:20]

    # 处理模型返回的详细 Markdown 分析：1. **三文鱼**（说明）
    bold_items = re.findall(r'\*\*([^*]{1,12})\*\*', text)
    if bold_items:
        return _normalize_ingredients(bold_items)

    # 尝试匹配中文食材关键词（1-4个汉字 + 常见食物相关后缀）
    food_keywords = re.findall(
        r'[\u4e00-\u9fff]{1,4}(?:肉|鱼|虾|蟹|蛋|菜|瓜|豆|菇|菌|笋|椒|葱|姜|蒜|奶|油|酱|醋|酒|糖|盐|粉|面|米|果|仁|叶|花|茄|薯|卜|梨|桃|莓|橘|檬|蕉|芹|菠|白|胡|玉|木|土|紫|洋|西|南|冬|夏|春|秋)',
        text
    )
    if food_keywords:
        # 单字食材（葱姜蒜等）本身就是后缀字，正则匹配不到，需单独补齐。
        # 跳过已出现在已有关键词中的字（如 "鸡蛋" 已含 "鸡"/"蛋"）。
        for char in text:
            if char in _SINGLE_CHAR_FOODS and char not in food_keywords:
                if not any(char in kw for kw in food_keywords):
                    food_keywords.append(char)
        return list(dict.fromkeys(food_keywords))[:20]  # 去重保序

    # 顿号、逗号分割
    parts = re.split(r'[、，,]', text)
    ingredients = [p.strip() for p in parts if _valid_ingredient_length(p.strip())]
    if ingredients:
        return ingredients[:20]

    return []


def _normalize_ingredients(value: Any, fallback_text: str = "") -> list[str]:
    """确保 ingredients 一定是短食材名数组，避免整段模型说明进入前端。"""
    raw_items: list[str] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                raw_items.append(item)
            elif isinstance(item, dict):
                raw_items.extend(str(v) for v in item.values() if isinstance(v, str))
    elif isinstance(value, str):
        raw_items.extend(_extract_ingredients_from_text(value))

    if not raw_items and fallback_text:
        raw_items.extend(_extract_ingredients_from_text(fallback_text))

    cleaned = []
    blocked = {"食材", "图片", "蔬菜", "水果", "调料", "完整食材列表"}
    for item in raw_items:
        text = re.sub(r"[（(].*?[）)]", "", str(item))
        text = re.sub(r"^[\d.\s、-]+", "", text)
        text = re.sub(r"[*#：:，,。；;].*$", "", text).strip()
        if not _valid_ingredient_length(text):
            continue
        if text in blocked or any(word in text for word in ("以下", "根据", "图片", "列表")):
            continue
        if text not in cleaned:
            cleaned.append(text)

    if not cleaned and fallback_text:
        for item in _extract_ingredients_from_text(fallback_text):
            text = re.sub(r"[（(].*?[）)]", "", str(item))
            text = re.sub(r"^[\d.\s、-]+", "", text)
            text = re.sub(r"[*#：:，,。；;].*$", "", text).strip()
            if not _valid_ingredient_length(text):
                continue
            if text in blocked or any(word in text for word in ("以下", "根据", "图片", "列表")):
                continue
            if text not in cleaned:
                cleaned.append(text)
    return cleaned[:20]


def _normalize_confidence(value: Any) -> Literal["high", "medium", "low"]:
    if value in ("high", "medium", "low"):
        return value
    return "low"


def recognize_ingredients(image: bytes | str) -> VisionResult:
    
    """识别图片中的食材。
    Args:
        image: 图片文件原始字节 (bytes) 或 Base64 编码字符串（不含 data:xxx;base64, 前缀）。

    Returns:
        VisionResult: 包含自然语言描述、食材列表和置信度的结构化结果。
    """
    if isinstance(image, bytes):
        image_b64 = base64.b64encode(image).decode("utf-8")
    else:
        image_b64 = image

    image_url = f"data:image/jpeg;base64,{image_b64}"

    message = HumanMessage(content=[
        {
            "type": "text",
            "text": (
                "你是一个食材识别助手。每次请求都是全新的独立图片，请只根据当前这张图片识别，"
                "不要参考任何之前的图片、菜谱或对话。\n"
                "请识别图片中的食材，只关注可食用的食物和调料，忽略容器、桌面、背景、水印等非食材物体。\n\n"
                "要求：\n"
                "1. 食材名称用中文，尽量具体（如\"西红柿\"而非\"蔬菜\"）\n"
                "2. 如果图片中没有食材或无法识别，ingredients 返回空数组，confidence 为 low\n"
                "3. confidence: 食材清晰可辨为 high，部分模糊为 medium，难以确定或数量很少为 low\n"
                "4. raw_description 用一句话描述图片中的食材情况\n\n"
                "严格按以下 JSON 格式返回，不要包含其他文字：\n"
                '{"ingredients": ["食材1", "食材2"], "confidence": "high", "raw_description": "图片中包含..."}'
            ),
        },
        {"type": "image_url", "image_url": {"url": image_url}},
    ])

    response = model.invoke([message])
    text = response.content.strip()
    # 处理 LLM 包裹在 ```json ... ``` 里的情况
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # LLM 返回了非标准 JSON，尝试从文本中提取食材
        ingredients = _normalize_ingredients([], text)
        return VisionResult(
            raw_description=text[:200],
            ingredients=ingredients,
            confidence="low",
        )
    if not isinstance(data, dict):
        return VisionResult(
            raw_description=text[:200],
            ingredients=_normalize_ingredients([], text),
            confidence="low",
        )

    return VisionResult(
        raw_description=str(
            data.get("raw_description")
            or data.get("rawDescription")
            or text[:200]
        )[:200],
        ingredients=_normalize_ingredients(data.get("ingredients"), text),
        confidence=_normalize_confidence(data.get("confidence")),
    )



