from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    groq_api_key: str = Field(..., description="Groq API key")
    database_url: str = Field(..., description="PostgreSQL connection URL")
    groq_model: str = Field(default="llama-3.3-70b-versatile")
    max_retry_attempts: int = Field(default=3)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
