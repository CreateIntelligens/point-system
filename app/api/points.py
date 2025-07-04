from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import asc, desc
from typing import Optional, Literal
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
    sort: Optional[str] = Query(
        default=None,
        description="排序方式：多個排序條件用逗號分隔，如 '-id,uid,point_rule_id'。支援欄位：id、uid、point_rule_id，加 '-' 前綴表示降序"
    ),
    db: AsyncSession = Depends(get_tenant_db)
):
    """
    獲取交易記錄列表
    
    - **sort**: 排序參數，支援多重排序，用逗號分隔：
        - 支援欄位：`id`、`uid`、`point_rule_id`
        - 降序請加 `-` 前綴，如：`-id`
        - 範例：`-id,uid,point_rule_id`
        - 每個欄位只取第一次出現的值
    """
    query = select(Transaction)
    
    # 添加排序邏輯
    if sort:
        sort_fields = [s.strip() for s in sort.split(",")]
        seen_fields = set()
        order_clauses = []
        
        for field in sort_fields:
            if field.startswith("-"):
                field_name = field[1:]
                direction = desc
            else:
                field_name = field
                direction = asc
            
            # 只處理第一次出現的欄位
            if field_name not in seen_fields and field_name in ["id", "uid", "point_rule_id"]:
                seen_fields.add(field_name)
                if field_name == "id":
                    order_clauses.append(direction(Transaction.id))
                elif field_name == "uid":
                    order_clauses.append(direction(Transaction.uid))
                elif field_name == "point_rule_id":
                    order_clauses.append(direction(Transaction.point_rule_id))
        
        if order_clauses:
            query = query.order_by(*order_clauses)

    result = await db.execute(query)
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
