from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from app.db.session import get_db
from app.models.merchant import Merchant, MerchantApiKey
from app.models.base import TenantBase
# Import models to register them with TenantBase metadata
from app.models.point_rule import PointRule
from app.models.transaction import Transaction
from sqlalchemy.exc import IntegrityError
import secrets
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/merchants", tags=["merchants"])

@router.post("/register")
async def register_merchant(name: str, db: AsyncSession = Depends(get_db)):
    merchant = Merchant(name=name)
    db.add(merchant)
    try:
        await db.commit()
        await db.refresh(merchant)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Merchant already exists")

    # Multi-tenancy: create schema and tables for merchant
    schema_name = f"merchant_{merchant.id}"
    await db.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
    await db.commit()
    # Set search_path and create tables in new schema
    await db.execute(text(f'SET search_path TO "{schema_name}", public'))
    
    # Create tables in the new schema using engine
    from app.db.session import engine
    async with engine.begin() as conn:
        # Set schema context for table creation
        await conn.execute(text(f'SET search_path TO "{schema_name}", public'))
        # Create all tenant tables (point_rules and transactions) with shared metadata
        await conn.run_sync(TenantBase.metadata.create_all)
    
    await db.execute(text('SET search_path TO public'))
    await db.commit()

    return {"code": 0, "message": "Merchant registered", "data": {"id": merchant.id, "name": merchant.name}}

@router.get("/", summary="List all merchants")
async def list_merchants(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Merchant))
    merchants = result.scalars().all()
    return {"code": 0, "message": "success", "data": [{"id": m.id, "name": m.name, "created_at": m.created_at.isoformat()} for m in merchants]}

@router.get("/{merchant_id}", summary="Get merchant by id")
async def get_merchant(merchant_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return {"code": 0, "message": "success", "data": {"id": merchant.id, "name": merchant.name, "created_at": merchant.created_at.isoformat()}}

@router.post("/{merchant_id}/apikey")
async def create_api_key(merchant_id: int, expires_in_days: int = 30, db: AsyncSession = Depends(get_db)):
    api_key = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=expires_in_days)
    key = MerchantApiKey(
        merchant_id=merchant_id,
        api_key=api_key,
        expires_at=expires_at,
        is_active=True,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    return {
        "code": 0,
        "message": "API key created",
        "data": {
            "api_key": key.api_key,
            "expires_at": key.expires_at.isoformat(),
            "is_active": key.is_active,
        }
    }

@router.get("/{merchant_id}/apikeys", summary="List API keys for a merchant")
async def list_api_keys(merchant_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MerchantApiKey).where(MerchantApiKey.merchant_id == merchant_id))
    keys = result.scalars().all()
    return {
        "code": 0,
        "message": "success",
        "data": [
            {
                "id": k.id,
                "api_key": k.api_key,
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "is_active": k.is_active,
                "scope": k.scope,
                "created_at": k.created_at.isoformat()
            }
            for k in keys
        ]
    }
