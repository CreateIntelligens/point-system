from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.merchants import router as merchants_router
from app.api.points import router as points_router
from app.db.session import engine
from app.db.base import MerchantBase
import asyncio
import logging
import traceback
from datetime import datetime
import os

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
log_filename = os.path.join(log_dir, f"log-{datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Point System API",
    version="1.0.0"
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception caught: {type(exc).__name__}: {str(exc)}")
    logger.error(f"Request: {request.method} {request.url}")
    logger.error(f"Traceback: {traceback.format_exc()}")
        
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "Internal Server Error", "data": None}
    )

@app.middleware("http")
async def unify_response(request: Request, call_next):
    # Don't wrap OpenAPI or Swagger static files
    if request.url.path.startswith("/openapi") or request.url.path.startswith("/docs") or request.url.path.startswith("/redoc"):
        return await call_next(request)
    response = await call_next(request)
    if response.headers.get("content-type") == "application/json":
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        import json
        try:
            data = json.loads(body)
        except Exception:
            return response
        # Already unified
        if isinstance(data, dict) and set(data.keys()) >= {"code", "message", "data"}:
            return JSONResponse(content=data, status_code=response.status_code)
        return JSONResponse(
            content={"code": 0, "message": "success", "data": data},
            status_code=response.status_code,
        )
    return response

@app.on_event("startup")
async def on_startup():
    # Create tables for public schema (merchants, merchant_api_keys)
    async with engine.begin() as conn:
        await conn.run_sync(MerchantBase.metadata.create_all)

app.include_router(merchants_router)
app.include_router(points_router)

@app.get("/api/v1/ping")
def ping():
    return {"code": 0, "message": "pong", "data": None}
