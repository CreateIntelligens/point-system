from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, text
from app.models.transaction import Transaction
from sqlalchemy.exc import SQLAlchemyError

async def insert_transaction_with_lock(
    db: AsyncSession,
    uid: str,
    point_rule_id: int,
    amount: float,
    detail: dict = None
):
    # Acquire advisory lock based on uid+point_rule_id hash
    lock_id = abs(hash(f"{uid}:{point_rule_id}")) % (2**63)
    await db.execute(text(f"SELECT pg_advisory_xact_lock({lock_id})"))

    # Get latest balance for this uid+point_rule_id
    result = await db.execute(
        select(Transaction.balance)
        .where(Transaction.uid == uid)
        .where(Transaction.point_rule_id == point_rule_id)
        .order_by(desc(Transaction.id))
        .limit(1)
    )
    last_balance = result.scalar_one_or_none()
    if last_balance is None:
        last_balance = 0.0

    new_balance = last_balance + amount

    tx = Transaction(
        uid=uid,
        point_rule_id=point_rule_id,
        amount=amount,
        balance=new_balance,
        detail=detail or {}
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return tx
