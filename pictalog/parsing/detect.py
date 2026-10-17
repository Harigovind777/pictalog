from pathlib import PurePath
from typing import Literal

FileKind = Literal["spreadsheet", "csv", "json", "docx", "pdf", "text", "image"]

KINDS: dict[str, FileKind] = {
    ".xlsx": "spreadsheet",
    ".xlsm": "spreadsheet",
    ".xls": "spreadsheet",
    ".ods": "spreadsheet",
    ".csv": "csv",
    ".tsv": "csv",
    ".json": "json",
    ".docx": "docx",
    ".pdf": "pdf",
    ".txt": "text",
    ".md": "text",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
    ".heic": "image",
}

ACCEPTED = ", ".join(KINDS)


class UnsupportedFile(ValueError):
    pass


def detect_kind(filename: str) -> FileKind:
    suffix = PurePath(filename).suffix.lower()
    if suffix in KINDS:
        return KINDS[suffix]
    if suffix == ".doc":
        raise UnsupportedFile("Old Word files (.doc) can't be read. Open it in Word and save it as .docx, then upload again.")
    raise UnsupportedFile(f"This file type isn't supported. Upload one of: {ACCEPTED}.")
