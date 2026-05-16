
"""
api_client.py · 封装所有对后端的 HTTP 请求
去掉食材管理相关接口，只保留：识图、Agent 对话、RAG 状态
"""

import requests
import json
import os
from typing import Generator

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


# ─────────────────────────────────────────────
# 图片识别
# ─────────────────────────────────────────────

def recognize_image(image_bytes: bytes, filename: str = "upload.jpg") -> tuple[bool, dict, str]:
    """上传图片 → GPT-4o Vision 识别食材，只返回食材列表，不写库"""
    try:
        files = {"file": (filename, image_bytes, "image/jpeg")}
        r = requests.post(f"{BACKEND_URL}/api/vision/recognize", files=files, timeout=30)
        data = r.json()
        return data.get("code") == 200, data.get("data", {}), data.get("message", "")
    except Exception as e:
        return False, {}, str(e)


def vision_chat(
    image_bytes: bytes,
    session_id: str,
    message: str = "",
    filename: str = "upload.jpg",
) -> tuple[bool, dict, str]:
    """图片 + 文字 → Agent 对话（非流式）"""
    try:
        files = {"file": (filename, image_bytes, "image/jpeg")}
        form  = {"sessionId": session_id, "message": message or "", "stream": "false"}
        r = requests.post(f"{BACKEND_URL}/api/vision/chat", files=files, data=form, timeout=60)
        resp = r.json()
        return resp.get("code") == 200, resp.get("data", {}), resp.get("message", "")
    except Exception as e:
        return False, {}, str(e)


# ─────────────────────────────────────────────
# Agent 对话
# ─────────────────────────────────────────────

def agent_chat_stream(session_id: str, message: str) -> Generator[str, None, None]:
    """纯文字流式对话，逐 token yield"""
    payload = {"sessionId": session_id, "message": message, "stream": True}
    try:
        with requests.post(
            f"{BACKEND_URL}/api/agent/chat",
            json=payload,
            stream=True,
            timeout=120,
        ) as r:
            for line in r.iter_lines():
                if line and line.startswith(b"data: "):
                    raw = line[6:].decode("utf-8")
                    try:
                        chunk = json.loads(raw)
                        if chunk.get("done"):
                            break
                        token = chunk.get("token", "")
                        if token:
                            yield token
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield f"\n[连接错误：{e}]"


def agent_chat(session_id: str, message: str) -> tuple[bool, dict, str]:
    """纯文字对话，非流式"""
    payload = {"sessionId": session_id, "message": message, "stream": False}
    try:
        r = requests.post(f"{BACKEND_URL}/api/agent/chat", json=payload, timeout=60)
        data = r.json()
        return data.get("code") == 200, data.get("data", {}), data.get("message", "")
    except Exception as e:
        return False, {}, str(e)


def clear_agent_session(session_id: str) -> tuple[bool, str]:
    try:
        r = requests.delete(f"{BACKEND_URL}/api/agent/clear/{session_id}", timeout=10)
        data = r.json()
        return data.get("code") == 200, data.get("message", "")
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────
# RAG 状态
# ─────────────────────────────────────────────

def get_rag_status() -> tuple[bool, dict, str]:
    try:
        r = requests.get(f"{BACKEND_URL}/api/rag/status", timeout=10)
        data = r.json()
        return data.get("code") == 200, data.get("data", {}), data.get("message", "")
    except Exception as e:
        return False, {}, str(e)