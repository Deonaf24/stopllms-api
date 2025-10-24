from fastapi import FastAPI
from app.routers import auth, generate, rag

def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(generate.router, tags=["llm"])
    app.include_router(rag.router, tags=["rag"])
    return app

app = create_app()

@app.get("/healthz")
def healthz():
    return {"ok": True}


