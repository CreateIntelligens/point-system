from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import TenantBase
from datetime import datetime

class Transaction(TenantBase):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, nullable=False, index=True)
    point_rule_id = Column(Integer, ForeignKey("point_rules.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    balance = Column(Float, nullable=False)
    detail = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("ix_transactions_detail_gin", "detail", postgresql_using="gin"),
    )
