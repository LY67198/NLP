"""
LangChain Agent 构建与会话管理。
使用 create_agent 创建具备 RAG 检索 + 联网搜索双工具的烹饪助手，
通过 InMemoryStore 实现跨会话的长期用户偏好记忆。
"""
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.store.memory import InMemoryStore
from langchain_core.messages import AIMessage, AIMessageChunk
from services.rag_service import retrieve_context
import langchain_openai.chat_models.base as _base
import os


# MIMO API 的 thinking 模式返回 reasoning_content，langchain-openai
# 不会保留这个字段，导致多轮对话时 API 报错。以下 patch 两个
# module-level 函数，保证 reasoning_content 在往返中不丢失。
_orig_convert_delta = _base._convert_delta_to_message_chunk
_orig_convert_message = _base._convert_message_to_dict


def _patched_convert_delta(_dict, default_class):
    msg_chunk = _orig_convert_delta(_dict, default_class)
    if "reasoning_content" in _dict and isinstance(msg_chunk, AIMessageChunk):
        msg_chunk.additional_kwargs["reasoning_content"] = _dict["reasoning_content"]
    return msg_chunk


def _patched_convert_message(message, api="chat/completions"):
    msg_dict = _orig_convert_message(message, api)
    if isinstance(message, AIMessage) and "reasoning_content" in message.additional_kwargs:
        msg_dict["reasoning_content"] = message.additional_kwargs["reasoning_content"]
    return msg_dict


_base._convert_delta_to_message_chunk = _patched_convert_delta
_base._convert_message_to_dict = _patched_convert_message


# 全局长期记忆
store = InMemoryStore()


tools = [retrieve_context]

system_prompt = """
你是一名私人厨师。收到用户提供的食材清单后，请按以下流程操作：
1.智能食谱检索：调用 retrieve_context 工具检索菜谱，该工具会自动优先本地知识库，本地无结果时自动联网搜索。
2.多维度评估与排序：从营养价值和制作难度两个维度对检索到的候选食谱进行量化打分，并根据得分排序，制作简单且营养丰富的排名靠前。
3.结构化方案输出：把排序后的食谱整理为一份结构清晰的建议报告，要包含食谱信息、得分、推荐理由，帮助用户快速做出决策。
4.持续对话：用户选择一道菜后，给出详细做法；后续可以追问替代食材、调整做法等。

请严格按照流程操作。工具返回结果可能包含来源标注，请不要在回复中重复这些标注——系统会自动追加来源信息。
"""
model = init_chat_model(
    model="mimo-v2-omni",
    model_provider="openai",
    api_key=os.getenv("MIMO_API_KEY"),
    base_url=os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1"),
)

_agents: dict = {}


def get_or_create_agent(session_id: str):
    """获取或创建指定会话的 Agent 实例。

    每个 session_id 对应一个独立的 Agent 实例，
    同一会话内的多轮对话共享上下文记忆。
    """
    if session_id not in _agents:
        _agents[session_id] = create_agent(
            model, tools, system_prompt=system_prompt
        )
    return _agents[session_id]


def clear_session(session_id: str) -> bool:
    """清除指定会话的 Agent 实例及记忆。"""
    if session_id in _agents:
        del _agents[session_id]
        return True
    return False
