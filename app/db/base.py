from app.models.merchant import Base as MerchantBase
from app.models.base import TenantBase

# For create_all, we need a single Base. We'll use MerchantBase for public schema,
# and TenantBase for tenant schemas.
