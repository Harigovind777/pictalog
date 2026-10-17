from pydantic_settings import BaseSettings, SettingsConfigDict


class HelperSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PICTALOG_HELPER_")

    server_url: str = "http://localhost:8000"
    worker_token: str = "dev-worker-token"
    ollama_url: str = "http://localhost:11434"
    image_model: str = "x/flux2-klein:4b"
    width: int = 768
    height: int = 768
    steps: int | None = None  # None = the model's own default
    text_model: str = "qwen3:4b"
    ocr_model: str = "glm-ocr"
    poll_seconds: float = 3.0
    heartbeat_seconds: float = 10.0
    timeout: float = 900.0
