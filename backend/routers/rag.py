from fastapi import APIRouter, File, Form, UploadFile

from services import rag_service

router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.post("/ingest")
async def ingest_recipe(
    file: UploadFile = File(..., description="菜谱文档 .txt / .md"),
    category: str = Form(None, description='分类标签，如"家常菜"'),
):
    # TODO: save uploaded file to a temp path, then call rag_service.ingest_file(path)
    return {
        "code": 200,
        "message": "入库成功",
        "data": {"filename": file.filename, "chunks_created": 0},
    }


@router.get("/status")
async def get_status():
    data = rag_service.get_status()
    return {"code": 200, "message": "success", "data": data}


@router.get("/search")
async def search(query: str, k: int = 3):
    results = rag_service.search_similar(query=query, k=k)
    return {"code": 200, "message": "success", "data": results}


