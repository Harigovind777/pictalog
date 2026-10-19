from pydantic_settings import BaseSettings, SettingsConfigDict


class HelperSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PICTALOG_HELPER_")

    server_url: str = "http://localhost:8000"
    worker_token: str = "dev-worker-token"
    ollama_url: str = "http://localhost:11434"
    image_model: str = "x/flux2-klein:4b"
    width: int = 768
    height: int = 768
    steps: int | None = 2  # 2 is ~2x faster than the model default with little visible difference; None = default
    # Reads lists, photos and scans in India's languages and writes the English photo descriptions. It must take
    # images (vision) and fit beside the image model: 3.3 GB + 5.7 GB of the ~11 GB the Mac lets the GPU use.
    text_model: str = "qwen3.5:4b"
    rewrite_prompts: bool = True  # plain-English product descriptions before making photos
    vision: bool = True  # the text model reads photos and scans itself, with Tesseract's words as a hint
    tesseract: bool = True  # use Tesseract when it's installed (brew install tesseract-lang)
    ocr_model: str = "qwen3.5:4b"  # with vision off: reads pages Tesseract can't (glm-ocr's own prompt if it's glm-ocr)
    poll_seconds: float = 3.0
    heartbeat_seconds: float = 10.0
    timeout: float = 900.0
