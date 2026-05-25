from fastapi import APIRouter

from services import rag_service

router = APIRouter(prefix="/api/rag", tags=["rag"])



@router.get("/status")
async def get_status():
    data = rag_service.get_status()
    return {"code": 200, "message": "success", "data": data}



# @router.get("/search")
# async def search(query: str, k: int = 3):
#     results = rag_service.search_similar(query=query, k=k)
#     return {"code": 200, "message": "success", "data": results}


