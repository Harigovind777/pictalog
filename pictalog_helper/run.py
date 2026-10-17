"""The image helper loop: ask the server for work, do it with local AI, send the result back."""

import logging
import threading
import time

import httpx

from pictalog_helper.client import ServerClient
from pictalog_helper.config import HelperSettings
from pictalog_helper.engines import CachingEngine, ImageEngine, OllamaImageEngine
from pictalog_helper.reader import DocumentReader

log = logging.getLogger("pictalog_helper")


def run_once(client: ServerClient, engine: ImageEngine, reader: DocumentReader) -> bool:
    """Do one job if there is one. Returns False when the queue was empty."""
    job = client.claim()
    if job is None:
        return False
    job_id, payload = job["id"], job["payload"]
    started = time.monotonic()
    try:
        if job["kind"] == "image":
            client.send_image(job_id, engine.generate(payload["prompt"], payload["seed"]))
            log.info("image for product %s made in %.0fs", payload.get("variant_id"), time.monotonic() - started)
        elif job["kind"] == "extract":
            text = payload.get("text")
            file = None if text else client.download(job_id)
            items = reader.read(text=text, file=file, filename=payload.get("filename") or "")
            client.send_items(job_id, items)
            log.info("read %s: %d products in %.0fs", payload.get("filename"), len(items), time.monotonic() - started)
        else:
            client.fail(job_id, f"This helper doesn't know how to do {job['kind']!r} jobs.")
    except Exception as e:  # report every failure so the job can be retried, then keep going
        log.warning("job %s failed: %s", job_id, e)
        client.fail(job_id, str(e) or e.__class__.__name__)
    return True


def _heartbeat(client: ServerClient, every: float, stop: threading.Event) -> None:
    """Tell the server we're alive even while a slow image is being made."""
    while not stop.wait(every):
        try:
            client.heartbeat()
        except httpx.HTTPError:
            pass


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
    settings = HelperSettings()
    client = ServerClient(settings)
    engine = CachingEngine(OllamaImageEngine(settings))
    reader = DocumentReader(settings)
    log.info("Pictalog image helper: %s → %s (images: %s, text: %s)",
             settings.ollama_url, settings.server_url, settings.image_model, settings.text_model)
    stop = threading.Event()
    threading.Thread(target=_heartbeat, args=(client, settings.heartbeat_seconds, stop), daemon=True).start()
    offline = False
    try:
        while True:
            try:
                worked = run_once(client, engine, reader)
                if offline:
                    log.info("connected to the Pictalog server again")
                offline = False
            except httpx.HTTPError as e:
                if not offline:
                    log.warning("can't reach the Pictalog server (%s); retrying", e)
                offline, worked = True, False
            if not worked:
                time.sleep(settings.poll_seconds)
    except KeyboardInterrupt:
        log.info("stopped")
    finally:
        stop.set()
