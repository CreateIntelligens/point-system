import os
import json
import logging
from datetime import datetime
from typing import Union, Dict, List, Any
from app.core.config import settings
from app.utils.timezone import timezone_manager

class CustomLogger:
    """自定義 Logger 類，支援自動日期檔名和多種數據格式"""
    
    def __init__(self):
        self.log_dir = settings.log_dir
        self.setup_log_directory()
        
    def setup_log_directory(self):
        """確保日誌目錄存在"""
        os.makedirs(self.log_dir, exist_ok=True)
    
    def get_log_filename(self) -> str:
        """根據配置時區生成日誌檔案名稱"""
        date_str = timezone_manager.format_date_for_filename()
        return os.path.join(self.log_dir, f"log-{date_str}.log")
    
    def get_logger(self) -> logging.Logger:
        """取得配置好的 logger"""
        log_filename = self.get_log_filename()
        
        # 創建 logger
        logger = logging.getLogger('app_logger')
        logger.setLevel(getattr(logging, settings.log_level.upper()))
        
        # 避免重複添加 handler
        if not logger.handlers:
            # 文件 handler
            file_handler = logging.FileHandler(log_filename, encoding='utf-8')
            file_handler.setLevel(getattr(logging, settings.log_level.upper()))
            
            # 控制台 handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, settings.log_level.upper()))
            
            # 格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def format_message(self, data: Union[str, Dict, List, Any]) -> str:
        """格式化訊息，支援多種數據類型"""
        if isinstance(data, str):
            return data
        elif isinstance(data, (dict, list)):
            return json.dumps(data, ensure_ascii=False, indent=2, default=str)
        else:
            return str(data)
    
    def log(self, data: Union[str, Dict, List, Any], level: str = 'INFO'):
        """記錄日誌"""
        logger = self.get_logger()
        message = self.format_message(data)
        
        # 添加時區資訊的時間戳
        timestamp = timezone_manager.format_datetime()
        formatted_message = f"[{timestamp}] {message}"
        
        level = level.upper()
        if hasattr(logger, level.lower()):
            getattr(logger, level.lower())(formatted_message)
        else:
            logger.info(formatted_message)
    
    def info(self, data: Union[str, Dict, List, Any]):
        """記錄 INFO 級別日誌"""
        self.log(data, 'INFO')
    
    def error(self, data: Union[str, Dict, List, Any]):
        """記錄 ERROR 級別日誌"""
        self.log(data, 'ERROR')
    
    def warning(self, data: Union[str, Dict, List, Any]):
        """記錄 WARNING 級別日誌"""
        self.log(data, 'WARNING')
    
    def debug(self, data: Union[str, Dict, List, Any]):
        """記錄 DEBUG 級別日誌"""
        self.log(data, 'DEBUG')

# 全域 logger 實例
app_logger = CustomLogger()

# 便捷函數
def logger(data: Union[str, Dict, List, Any], level: str = 'INFO'):
    """便捷的日誌記錄函數"""
    app_logger.log(data, level)
