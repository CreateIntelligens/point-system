from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.core.security import get_current_tenant, get_tenant_db
from app.models.point_rule import PointRule
from app.models.transaction import Transaction
from app.services.transaction_service import insert_transaction_with_lock
from app.utils.logger import logger
from app.utils.timezone import timezone_manager

router = APIRouter(prefix="/api/v1/points", tags=["points"])

# PointRule CRUD

@router.post("/rules")
async def create_point_rule(
    name: str,
    rate: float,
    description: str = "",
    db: AsyncSession = Depends(get_tenant_db)
):
    logger({
        "action": "create_point_rule",
        "name": name,
        "rate": rate,
        "description": description
    })
    
    rule = PointRule(name=name, rate=rate, description=description)
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    logger(f"積分規則創建成功: ID={rule.id}, Name={rule.name}")
    
    return {"code": 0, "message": "created", "data": {"id": rule.id, "name": rule.name, "rate": rule.rate, "description": rule.description}}

@router.get("/rules")
async def list_point_rules(
    db: AsyncSession = Depends(get_tenant_db)
):
    result = await db.execute(select(PointRule))
    rules = result.scalars().all()
    return {"code": 0, "message": "success", "data": [{"id": r.id, "name": r.name, "rate": r.rate, "description": r.description} for r in rules]}

@router.put("/rules/{rule_id}")
async def update_point_rule(
    rule_id: int,
    name: str = None,
    rate: float = None,
    description: str = None,
    db: AsyncSession = Depends(get_tenant_db)
):
    result = await db.execute(select(PointRule).where(PointRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    if name is not None:
        rule.name = name
    if rate is not None:
        rule.rate = rate
    if description is not None:
        rule.description = description
    await db.commit()
    await db.refresh(rule)
    return {"code": 0, "message": "updated", "data": {"id": rule.id, "name": rule.name, "rate": rule.rate, "description": rule.description}}

@router.delete("/rules/{rule_id}")
async def delete_point_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_tenant_db)
):
    result = await db.execute(select(PointRule).where(PointRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
    return {"code": 0, "message": "deleted", "data": None}

# Transaction Insert Only

@router.post("/transactions")
async def create_transaction(
    uid: str,
    point_rule_id: int,
    amount: float,
    detail: dict = None,
    db: AsyncSession = Depends(get_tenant_db)
):
    logger({
        "action": "create_transaction_via_points",
        "uid": uid,
        "point_rule_id": point_rule_id,
        "amount": amount,
        "detail": detail
    })
    
    tx = await insert_transaction_with_lock(
        db=db,
        uid=uid,
        point_rule_id=point_rule_id,
        amount=amount,
        detail=detail
    )
    
    logger(f"交易創建成功: ID={tx.id}, UID={tx.uid}, 餘額={tx.balance}")
    
    return {
        "code": 0,
        "message": "created",
        "data": {
            "id": tx.id,
            "uid": tx.uid,
            "point_rule_id": tx.point_rule_id,
            "amount": tx.amount,
            "balance": tx.balance,
            "detail": tx.detail,
            "created_at": timezone_manager.format_datetime(tx.created_at)
        }
    }

@router.get("/transactions")
async def list_transactions(
    db: AsyncSession = Depends(get_tenant_db)
):
    result = await db.execute(select(Transaction))
    logs = result.scalars().all()
    return {"code": 0, "message": "success", "data": [
        {
            "id": l.id,
            "uid": l.uid,
            "point_rule_id": l.point_rule_id,
            "amount": l.amount,
            "balance": l.balance,
            "detail": l.detail,
            "created_at": timezone_manager.format_datetime(l.created_at)
        }
        for l in logs
    ]}
