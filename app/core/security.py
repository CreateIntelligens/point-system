from fastapi import Header, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.models.merchant import MerchantApiKey, Merchant
from app.core.multi_tenancy import set_search_path
from datetime import datetime

class TenantContext:
    def __init__(self, merchant, schema_name, db_session):
        self.merchant = merchant
        self.schema_name = schema_name
        self.db_session = db_session

async def get_current_tenant(
    x_api_key: str = Header(..., alias="x-api-key"),
    db: AsyncSession = Depends(get_db)
):
    # 查詢 API key
    result = await db.execute(
        select(MerchantApiKey, Merchant)
        .join(Merchant, MerchantApiKey.merchant_id == Merchant.id)
        .where(MerchantApiKey.api_key == x_api_key)
        .where(MerchantApiKey.is_active == True)
        .where((MerchantApiKey.expires_at == None) | (MerchantApiKey.expires_at > datetime.now()))
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired x-api-key")
    api_key, merchant = row
    # 切換 schema
    schema_name = f"merchant_{merchant.id}"
    await set_search_path(db, schema_name)
    return TenantContext(merchant, schema_name, db)
