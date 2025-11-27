from __future__ import annotations
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile

from app.core.config import settings


class StorageError(Exception):
    """Raised when a storage operation fails."""


@dataclass
class StoredFile:
    path: str
    url: str | None
    size: int
    mime_type: str | None


class BaseStorage:
    async def save_upload(self, upload: UploadFile, assignment_id: int) -> StoredFile:  # pragma: no cover - interface
        raise NotImplementedError


class LocalStorage(BaseStorage):
    def __init__(self, base_dir: Path, base_url: Optional[str] = None):
        self.base_dir = base_dir
        self.base_url = base_url.rstrip("/") if base_url else None

    async def save_upload(self, upload: UploadFile, assignment_id: int) -> StoredFile:
        safe_name = Path(upload.filename or "upload").name
        key = f"assignments/{assignment_id}/{uuid4().hex}_{safe_name}"
        destination = self.base_dir / key
        destination.parent.mkdir(parents=True, exist_ok=True)

        size = 0
        with destination.open("wb") as buffer:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                buffer.write(chunk)
                size += len(chunk)

        await upload.seek(0)

        url = f"{self.base_url}/{key}" if self.base_url else None
        return StoredFile(path=key, url=url, size=size, mime_type=upload.content_type)


class S3Storage(BaseStorage):
    def __init__(
        self,
        bucket: str,
        base_url: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
    ):
        self.bucket = bucket
        self.base_url = base_url.rstrip("/") if base_url else None

        session = boto3.session.Session()
        self.client = session.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region_name,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self.region_name = region_name
        self.endpoint_url = endpoint_url.rstrip("/") if endpoint_url else None

    async def save_upload(self, upload: UploadFile, assignment_id: int) -> StoredFile:
        safe_name = Path(upload.filename or "upload").name
        key = f"assignments/{assignment_id}/{uuid4().hex}_{safe_name}"

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            size = 0
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                tmp.write(chunk)
                size += len(chunk)
            temp_path = Path(tmp.name)

        try:
            self.client.upload_file(
                Filename=str(temp_path),
                Bucket=self.bucket,
                Key=key,
                ExtraArgs={"ContentType": upload.content_type or "application/octet-stream"},
            )
        except (BotoCoreError, ClientError) as exc:  # pragma: no cover - passthrough
            raise StorageError("Failed to upload file to object storage") from exc
        finally:
            temp_path.unlink(missing_ok=True)

        await upload.seek(0)

        url = self._build_url(key)
        return StoredFile(path=key, url=url, size=size, mime_type=upload.content_type)

    def _build_url(self, key: str) -> str | None:
        if self.base_url:
            return f"{self.base_url}/{key}"
        if self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket}/{key}"
        if self.region_name:
            return f"https://{self.bucket}.s3.{self.region_name}.amazonaws.com/{key}"
        return None


_storage: BaseStorage | None = None


def get_storage_service() -> BaseStorage:
    global _storage
    if _storage:
        return _storage

    backend = settings.FILE_STORAGE_BACKEND.lower()
    if backend == "s3":
        if not settings.FILE_STORAGE_BUCKET:
            raise RuntimeError("FILE_STORAGE_BUCKET must be set for s3 backend")
        _storage = S3Storage(
            bucket=settings.FILE_STORAGE_BUCKET,
            base_url=settings.FILE_STORAGE_BASE_URL,
            endpoint_url=settings.FILE_STORAGE_S3_ENDPOINT,
            region_name=settings.FILE_STORAGE_S3_REGION,
            access_key=settings.FILE_STORAGE_S3_ACCESS_KEY,
            secret_key=settings.FILE_STORAGE_S3_SECRET_KEY,
        )
    else:
        base_dir = Path(settings.FILE_STORAGE_DIR)
        _storage = LocalStorage(base_dir=base_dir, base_url=settings.FILE_STORAGE_BASE_URL)

    return _storage
