import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import create_pool, close_pool

logger = logging.getLogger("fiberq")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Starting FiberQ API server")

    os.makedirs(settings.storage_photos_dir, exist_ok=True)
    os.makedirs(settings.storage_gpkg_dir, exist_ok=True)

    await create_pool()
    logger.info("Database pool created")

    yield

    await close_pool()
    logger.info("Database pool closed")


app = FastAPI(
    title="FiberQ API",
    description="REST API for FiberQ fiber optic network management",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    from database import get_pool
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchval("SELECT 1")
    return {"status": "ok", "db": result == 1}


# --- Register routers -------------------------------------------------------

from auth.routes import router as auth_router
from projects.routes import router as projects_router
from sync.routes import router as sync_router
from fiber_plan.routes import router as fiber_plan_router
from work_orders.routes import router as work_orders_router

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(projects_router, prefix="/projects", tags=["projects"])
app.include_router(sync_router, prefix="/sync", tags=["sync"])
app.include_router(fiber_plan_router, prefix="/fiber-plan", tags=["fiber-plan"])
app.include_router(work_orders_router, prefix="/work-orders", tags=["work-orders"])
