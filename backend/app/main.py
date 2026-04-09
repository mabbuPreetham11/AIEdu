from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.core.config import ensure_local_directories, settings
from app.core.exceptions import add_exception_handlers
from app.core.rate_limit import limiter
from app.db.seed import seed_demo_data
from app.db.session import close_db, init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_local_directories()
    await init_db()
    if settings.seed_demo_data:
        await seed_demo_data()
    yield
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)
app.mount("/uploads", StaticFiles(directory=settings.local_storage_path, check_dir=False), name="uploads")


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
