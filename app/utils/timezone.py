from datetime import datetime, timezone
from typing import Optional, Union
import pytz
from app.core.config import settings

class TimezoneManager:
    """統一時區管理器"""
    
    def __init__(self):
        self.timezone = pytz.timezone(settings.timezone)
    
    def now(self) -> datetime:
        """取得目前配置時區的時間"""
        return datetime.now(self.timezone)
    
    def localize(self, dt: datetime) -> datetime:
        """將 naive datetime 轉換為配置時區的 aware datetime"""
        if dt.tzinfo is None:
            return self.timezone.localize(dt)
        return dt.astimezone(self.timezone)
    
    def format_date_for_filename(self) -> str:
        """取得用於檔案名稱的日期格式"""
        return self.now().strftime('%Y-%m-%d')
    
    def format_datetime(self, dt: Optional[datetime] = None, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
        """格式化時間"""
        if dt is None:
            dt = self.now()
        elif dt.tzinfo is None:
            dt = self.localize(dt)
        else:
            dt = dt.astimezone(self.timezone)
        return dt.strftime(fmt)

# 全域時區管理器實例
timezone_manager = TimezoneManager()
