from fastapi import APIRouter, HTTPException, Request, Response

router = APIRouter(prefix="/api/files")


@router.get("/{key:path}")
def get_file(key: str, request: Request) -> Response:
    # Only generated/uploaded images are public; uploaded catalog files never are.
    if not key.startswith("img/") or ".." in key.split("/"):
        raise HTTPException(404, "File not found.")
    try:
        data = request.app.state.storage.read(key)
    except KeyError:
        raise HTTPException(404, "File not found.") from None
    return Response(data, media_type="image/webp", headers={"Cache-Control": "public, max-age=31536000"})
