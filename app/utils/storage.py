from pathlib import Path
from uuid import uuid4

from starlette.concurrency import run_in_threadpool

from app.core.config import settings

ALLOWED_SUFFIXES = {".mp3", ".wav", ".m4a", ".ogg"}


def _build_path(filename: str) -> Path:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        suffix = ".mp3"
    return Path(settings.storage_dir) / f"{uuid4().hex}{suffix}"


async def save_audio(filename: str, content: bytes) -> str:
    path = _build_path(filename)
    await run_in_threadpool(path.parent.mkdir, parents=True, exist_ok=True)
    await run_in_threadpool(path.write_bytes, content)
    return str(path)
