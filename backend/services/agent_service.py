"""
LangChain Agent 构建与会话管理。
使用 create_agent 创建具备 RAG 检索 + 联网搜索双工具的烹饪助手，
通过 InMemoryStore 实现跨会话的长期用户偏好记忆。
"""

from typing import Any

# 实际类型为 langgraph.graph.state.CompiledStateGraph
AgentInstance = Any


def get_or_create_agent(session_id: str) -> AgentInstance:
    """获取或创建指定会话的 Agent 实例。

    每个 session_id 对应一个独立的 Agent 实例，
    同一会话内的多轮对话共享上下文记忆。

    Args:
        session_id: 会话唯一标识。前端首次传 "new" 时由路由层生成新的 session_id。

    Returns:
        AgentInstance: LangGraph Agent 实例，支持 .invoke() 和 .astream()。
    """


def clear_session(session_id: str) -> bool:
    """清除指定会话的 Agent 实例及记忆。

    Args:
        session_id: 要清除的会话 ID。

    Returns:
        bool: 清除成功返回 True，会话不存在返回 False。
    """
