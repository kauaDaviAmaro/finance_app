from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: Optional[str] = None
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    
    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # App
    app_name: str = "Finances API"
    debug: bool = True
    
    # Celery
    celery_broker_url: str
    celery_result_backend: str
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
        
    def get_database_url(self) -> str:
        """Constrói a URL do banco de dados a partir das variáveis individuais"""
        if all([self.db_user, self.db_password, self.db_host, self.db_port, self.db_name]):
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        if self.database_url:
            return self.database_url
        raise ValueError("Either database_url or all individual database parameters (db_user, db_password, db_host, db_port, db_name) must be provided")

settings = Settings()