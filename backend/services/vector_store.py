"""
ChromaDB 向量库初始化与懒加载。
使用 HuggingFace 中文嵌入模型，本地持久化到 data/chroma_db/。
"""

from pathlib import Path
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
RECIPES_DIR = BASE_DIR / "data" / "recipes"
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"

_embedding_model = HuggingFaceEmbeddings(model_name="shibing624/text2vec-base-chinese")

_vector_store = None


def get_vector_store() -> Chroma:
    """获取全局 ChromaDB 向量库实例（懒加载）。

    首次调用时初始化，后续调用返回同一实例。
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = Chroma(
            collection_name="recipes",
            embedding_function=_embedding_model,
            persist_directory=str(CHROMA_DIR),
        )
    return _vector_store
