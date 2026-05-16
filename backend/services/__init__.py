"""服务层：向量库、识图、RAG 检索、联网搜索、Agent 会话管理。"""

from services.vector_store import get_vector_store
from services.vision_service import recognize_ingredients, recognize_ingredients_b64, VisionResult
from services.rag_service import ingest_file, search_similar, get_status, retrieve_context
from services.search_service import web_search
from services.agent_service import get_or_create_agent, clear_session

__all__ = [
    # vector_store
    "get_vector_store",
    # vision_service
    "recognize_ingredients",
    "recognize_ingredients_b64",
    "VisionResult",
    # rag_service
    "ingest_file",
    "search_similar",
    "get_status",
    "retrieve_context",
    # search_service
    "web_search",
    # agent_service
    "get_or_create_agent",
    "clear_session",
]
