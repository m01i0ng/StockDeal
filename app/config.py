from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    cache_warmup_enabled: bool = True
    db_auto_migrate: bool = True
    scheduler_enabled: bool = True
    scheduler_confirm_hour: int = 9
    scheduler_confirm_minute: int = 0
    redis_url: str = "redis://localhost:6379/0"
    database_url: str | None = None
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "password"
    mysql_database: str = "stock_deal"
    nowapi_appkey: str = ""
    nowapi_sign: str = ""
    nowapi_base_url: str = "https://sapi.k780.com"
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    log_max_bytes: int = 10 * 1024 * 1024
    log_backup_count: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    def model_post_init(self, __context: dict) -> None:
        if self.database_url:
            return
        self.database_url = (
            "mysql+pymysql://"
            f"{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )


settings = Settings()
