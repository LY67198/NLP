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
    loader = TextLoader(file_path=file_path)
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


@tool
def retrieve_context(query:str,k:int=3):
    """【Agent 工具】优先调用，在本地菜谱知识库中语义检索匹配菜谱。

    若本地库无相关结果，Agent 应转而调用 web_search 联网搜索。
    """
    vector_store = get_vector_store()
   

    if  vector_store is None:
        result=web_search(query) 
    else:
        docs = vector_store.similarity_search(query=query,k=k)
        if docs:
            result = "\n\n".join(doc.page_content for doc in docs)
        else:
            result= web_search(query)

    return result



