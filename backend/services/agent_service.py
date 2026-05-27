from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.store.memory import InMemoryStore
from langchain_core.messages import AIMessage, AIMessageChunk
from services.rag_service import retrieve_context
from services.search_service import web_search
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


tools = [retrieve_context, web_search]

system_prompt = """
你是一名私人厨师。根据用户意图，你需要判断该走哪种模式：

**A. 用户列出食材但不确定做什么**（如"我有鸡蛋和西红柿，能做什么？"）
1. 调用 retrieve_context 检索相关菜谱。
2. 从营养价值和制作难度两个维度对候选食谱量化打分，按得分排序（简单且营养的靠前）。
3. 输出结构清晰的推荐报告，包含食谱信息、得分、推荐理由。
4. 等待用户选择，用户选定后给出详细做法。

**B. 用户已经指定了具体菜名**（如"三文鱼时蔬沙拉怎么做？"、"我要做回锅肉"、"第一道菜怎么做"、"第二道菜做法"）
1. 调用 retrieve_context 直接检索该菜的做法。
2. 直接输出完整的烹饪教程，包括：
   - 完整食材清单及用量
   - 分步骤烹饪指导
   - 烹饪小贴士和替代方案
3. 不要做评分、排名或多菜对比——用户已经知道要做什么，只需要做法。

**关键判断：** 只要用户提到了具体菜名，就选 B 模式。只有用户单纯列出食材且没有指定菜名时，才走 A 模式。

**工具使用规则（重要！严格遵守）：**
- 第一步：调用 retrieve_context 搜索本地菜谱知识库。
- 第二步：判断返回结果是否匹配。
  - 如果 retrieve_context 返回内容包含“【数据来源：本地知识库】”，请先检查返回的菜谱中是否确实包含用户的核心食材。如果用户提到的食材在返回结果中完全未出现，说明实际未命中，必须调用 web_search。确认命中后才可直接使用这些结果回复用户，严禁再调用 web_search。
  - 如果 retrieve_context 返回“本地知识库中未找到”或提示相关度低，必须调用 web_search，不能用模型常识补全菜谱。
  - 只有在返回结果明显不匹配（如用户要墨西哥菜、意大利菜、日料等本地库没有的菜系），或未返回任何结果时，才调用 web_search。
- 严禁自行编造菜谱，你只能推荐工具返回结果中实际存在的菜谱。

请严格按照上述规则操作。工具返回结果可能包含来源标注，请不要在回复中重复这些标注——系统会自动追加来源信息。
"""
model = init_chat_model(
    model="mimo-v2.5",
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
