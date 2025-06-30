from fastapi import FastAPI
from app.api.merchants import router as merchants_router
from app.db.session import engine
from app.db.base import MerchantBase
import asyncio

from fastapi.responses import JSONResponse
from fastapi.requests import Request

app = FastAPI(
    title="Point System API",
    version="1.0.0"
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

@app.get("/api/v1/ping")
def ping():
    return {"code": 0, "message": "pong", "data": None}
