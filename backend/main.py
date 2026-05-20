from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import agent, rag
from services.rag_service import ingest_file, get_status


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：向量库为空则自动导入菜谱
    status = get_status()
    if status["total_chunks"] == 0:
        ingest_file()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"msg": "hello"}


app.include_router(agent.router)
app.include_router(rag.router)

