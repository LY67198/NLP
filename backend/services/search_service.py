from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults


tavily = TavilySearchResults(max_results=5, search_depth="advanced", include_answer=True)


@tool
def web_search(query:str)->str:
    """【Agent 工具】当本地菜谱库未找到相关结果时调用。

    联网搜索菜谱做法，自动为查询补充"菜谱做法"关键词。
    """

    if '菜谱' not in query and "做法" not in query:
        query += "菜谱做法"
    results = tavily.invoke(query)
    if not results:
        return "未找到相关搜索结果。"
    
    return "\n\n".join(
        f"【{r.get('title','')}】\n{r.get('content','')}\n来源：{r.get('url','')}"
        for r in results
    )


