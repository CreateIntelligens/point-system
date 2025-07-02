import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 應用設定
    app_name: str = "Point System API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 統一時區設定
    timezone: str = "Asia/Taipei"
    
    # 日誌設定
    log_level: str = "INFO"
    log_dir: str = "app/logs"
    
    # 資料庫設定
    database_url: Optional[str] = None
    
    class Config:
        env_file = "app/.env"
        case_sensitive = False

# 全域設定實例
settings = Settings()
