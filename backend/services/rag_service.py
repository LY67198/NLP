from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from services.vector_store import get_vector_store, RECIPES_DIR
from langchain.tools import tool
from services.search_service import web_search


def ingest_file(file_path: str | None = None) -> list[str]:
    """将菜谱文档分块向量化并存入 ChromaDB。

    Args:
        file_path: 菜谱文档路径（.txt / .md）。为 None 时默认使用 data/recipes/recipes_dataset.txt。

    Returns:
        list[str]: 入库后每条 chunk 对应的向量库文档 ID 列表。
    """
    if file_path is None:
        file_path = str(RECIPES_DIR / "recipes_dataset.txt")
    loader = TextLoader(file_path=file_path, encoding="utf-8")
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = text_splitter.split_documents(docs)
    ids = get_vector_store().add_documents(chunks)
    return ids


def search_similar(query: str, k: int = 3) -> list[dict]:
    """在本地菜谱库中语义检索，返回最相似的 k 个菜谱片段。

    Args:
        query: 检索查询字符串，如 "西红柿炒鸡蛋"。
        k:    返回结果数量，默认 3。

    Returns:
        list[dict]: 每个元素为 {"content": 文档内容, "metadata": 元信息}。
    """
    vector_store = get_vector_store()
    docs = vector_store.similarity_search(query=query, k=k)
    return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]


def get_status() -> dict:
    """获取向量库状态，返回已入库的文档片段总数。

    Returns:
        dict: 如 {"total_chunks": 156}。
    """
    count = get_vector_store()._collection.count()
    return {"total_chunks": count}


RELEVANCE_THRESHOLD = 0.6  # 相关性阈值（0-1），低于此值的本地结果视为不匹配，回退网络搜索


@tool
def retrieve_context(query: str, k: int = 3):
    """【Agent 工具】在本地菜谱知识库中语义检索匹配菜谱。

    自动判断结果相关性：高质量匹配 → 本地知识库，无关结果 → 自动回退网络搜索。
    """
    vector_store = get_vector_store()

    if vector_store is None:
        return "【数据来源：网络搜索】\n\n" + web_search.invoke({"query": query})

    docs_with_scores = vector_store.similarity_search_with_relevance_scores(query=query, k=k)
    relevant = [(doc, score) for doc, score in docs_with_scores if score >= RELEVANCE_THRESHOLD]

    if relevant:
        lines = [f"{doc.page_content}" for doc, _ in relevant]
        return "【数据来源：本地知识库】\n\n" + "\n\n".join(lines)
    else:
        return "【数据来源：网络搜索】\n\n" + web_search.invoke({"query": query})
