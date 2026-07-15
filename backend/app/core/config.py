from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn

class Settings(BaseSettings):
    PROJECT_NAME: str = "Payment Verification API"
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()