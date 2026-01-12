from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.routers import analytics, assignments, auth, classes, generate, rag, users, stream, materials
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI()
    if settings.FILE_STORAGE_BACKEND.lower() == "local" and settings.FILE_STORAGE_BASE_URL:
        mount_path = settings.FILE_STORAGE_BASE_URL.rstrip("/") or "/"
        if not mount_path.startswith("/"):
            mount_path = f"/{mount_path}"
        app.mount(
            mount_path,
            StaticFiles(directory=settings.FILE_STORAGE_DIR),
            name="file-storage",
        )
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(generate.router, tags=["llm"])
    app.include_router(rag.router, tags=["rag"])
    app.include_router(users.router, tags=["school"])
    app.include_router(classes.router, tags=["school"])
    app.include_router(assignments.router, tags=["school"])
    app.include_router(analytics.router)
    app.include_router(stream.router)
    app.include_router(materials.router)
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
