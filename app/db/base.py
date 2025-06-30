from app.models.merchant import Base as MerchantBase
from app.models.point_rule import Base as PointRuleBase
from app.models.point_log import Base as PointLogBase

# For create_all, we need a single Base. We'll use MerchantBase for public schema,
# and PointRuleBase/PointLogBase for tenant schemas.
