import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from ...config import settings


async def save_upload(file: UploadFile, prefix: str = "watch") -> str:
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "image.jpg").suffix.lower() or ".jpg"
    filename = f"{prefix}-{uuid4().hex}{ext}"
    destination = Path(settings.uploads_dir) / filename
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return filename


def upload_path(filename: str) -> str:
    return str(Path(settings.uploads_dir) / filename)
