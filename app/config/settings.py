from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    wecom_window_title: str = "企业微信"
    rpa_step_delay: float = 0.5
    rpa_search_wait: float = 1.0
    rpa_send_wait: float = 0.5
    max_retry_count: int = 3
    retry_delay_seconds: int = 30
    scheduler_interval: int = 5
    database_url: str = "sqlite:///./data/tasks.db"
    screenshot_dir: str = "./screenshots"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # 用户映射文件路径
    user_mapping_file: str = "./config/user_mapping.json"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
