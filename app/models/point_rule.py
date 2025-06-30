from sqlalchemy import Column, Integer, String, Float
from app.models.base import TenantBase

class PointRule(TenantBase):
    __tablename__ = "point_rules"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    rate = Column(Float, nullable=False)
    description = Column(String, nullable=True)
