from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn

class Settings(BaseSettings):
    PROJECT_NAME: str = "Payment Verification API"
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    BASE_VERIFICATION_URL: str = "https://verify.example.com/pay"
    DEFAULT_INVOICE_EXPIRE_MINUTES: int = 60
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()