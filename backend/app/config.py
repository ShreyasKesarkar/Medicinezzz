import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Check for .env in current cwd or BASE_DIR
env_file_path = BASE_DIR / ".env"
if not env_file_path.exists():
    env_file_path = Path(".env")

class Settings(BaseSettings):
    database_url: str = Field(..., validation_alias="DATABASE_URL")
    supabase_url: str = Field(..., validation_alias="SUPABASE_URL")
    supabase_anon_key: str = Field(..., validation_alias="SUPABASE_ANON_KEY")
    port: int = Field(8000, validation_alias="PORT")
    environment: str = Field("development", validation_alias="ENVIRONMENT")
    allowed_origins: str = Field("", validation_alias="ALLOWED_ORIGINS")
    
    model_config = SettingsConfigDict(
        env_file=str(env_file_path) if env_file_path.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
