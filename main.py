from fastapi import FastAPI
from api.document_upload import router

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Doctor Agent API"}

app.include_router(router, prefix="/api")



