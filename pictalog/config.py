from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PICTALOG_")

    database_url: str = "sqlite:///data/pictalog.db"
    storage_dir: Path = Path("data/files")
    secret_key: str = "dev-secret-change-me-before-going-online"
    worker_token: str = "dev-worker-token"
    max_upload_mb: int = 25
    token_days: int = 30
