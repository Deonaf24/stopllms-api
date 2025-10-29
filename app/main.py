from fastapi import FastAPI
from app.routers import auth, generate, rag
from fastapi.middleware.cors import CORSMiddleware

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

origins = [
    "http://localhost:3000",   # Next.js dev
    "http://127.0.0.1:3000",   # sometimes this variant is used
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # or ["*"] for testing only
    allow_credentials=True,
    allow_methods=["*"],         # allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],         # allow all headers
)
