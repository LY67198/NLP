from fastapi import FastAPI
from routers import agent, rag

app = FastAPI()


@app.get("/")
async def root():
    return {"msg": "hello"}


app.include_router(agent.router)
app.include_router(rag.router)

