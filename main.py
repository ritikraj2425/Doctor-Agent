import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.document_upload import router
from api.auth import router as auth_router
from api.chats import router as chats_router

app = FastAPI(
    title="DocAgent AI",
    description="Multi-Agent Clinical Decision Support & Triage Platform",
    version="2.0.0",
)

app.include_router(router, prefix="/api")
app.include_router(auth_router)
app.include_router(chats_router)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@app.get("/")
def read_root():
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))


@app.get("/health")
def health():
    return {"status": "healthy", "service": "DocAgent AI"}
