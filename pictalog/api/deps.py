from fastapi import HTTPException, Request, UploadFile

from pictalog.images import save_image


async def read_upload(upload: UploadFile, request: Request) -> bytes:
    """Read an uploaded file, refusing anything over the configured size limit."""
    max_mb = request.app.state.settings.max_upload_mb
    data = await upload.read(max_mb * 1024 * 1024 + 1)
    if len(data) > max_mb * 1024 * 1024:
        raise HTTPException(413, f"That file is too big. The limit is {max_mb} MB.")
    return data


def store_image(request: Request, data: bytes) -> tuple[str, str]:
    """Convert to WebP + thumbnail, save both, and return their storage keys."""
    try:
        return save_image(request.app.state.storage, data)
    except ValueError:
        raise HTTPException(400, "That file isn't an image we can read.") from None
