from pathlib import Path

import boto3

from app.core.config import settings


class StorageService:
    def __init__(self) -> None:
        self.client = None
        self.base_path = Path(settings.local_storage_path)
        if settings.storage_backend == "s3":
            self.client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region,
            )

    def upload_bytes(self, key: str, content: bytes, content_type: str) -> str:
        if self.client:
            self.client.put_object(Bucket=settings.s3_bucket, Key=key, Body=content, ContentType=content_type)
            return f"{settings.s3_endpoint_url}/{settings.s3_bucket}/{key}"

        destination = self.base_path / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return str(destination.resolve())
