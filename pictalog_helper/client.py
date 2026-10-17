import httpx

from pictalog_helper.config import HelperSettings


class ServerClient:
    """Talks to the Pictalog server's worker endpoints. Outbound only — nothing on the Mac listens for connections."""

    def __init__(self, settings: HelperSettings, transport: httpx.BaseTransport | None = None):
        self.engine = settings.image_model
        self._http = httpx.Client(
            base_url=settings.server_url,
            headers={"X-Worker-Token": settings.worker_token},
            timeout=60.0,
            transport=transport,
        )

    def claim(self) -> dict | None:
        res = self._http.post("/api/worker/claim", json={"engine": self.engine})
        res.raise_for_status()
        return None if res.status_code == 204 else res.json()

    def heartbeat(self) -> None:
        self._http.post("/api/worker/heartbeat", json={"engine": self.engine}).raise_for_status()

    def download(self, job_id: int) -> bytes:
        res = self._http.get(f"/api/worker/jobs/{job_id}/file")
        res.raise_for_status()
        return res.content

    def send_image(self, job_id: int, png: bytes) -> None:
        files = {"file": ("image.png", png, "image/png")}
        self._http.post(f"/api/worker/jobs/{job_id}/image", files=files).raise_for_status()

    def send_items(self, job_id: int, items: list[dict]) -> None:
        self._http.post(f"/api/worker/jobs/{job_id}/items", json={"items": items}).raise_for_status()

    def fail(self, job_id: int, error: str) -> None:
        self._http.post(f"/api/worker/jobs/{job_id}/fail", json={"error": error}).raise_for_status()
