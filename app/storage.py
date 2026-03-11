from __future__ import annotations

import logging
from pathlib import Path

import boto3
from botocore.config import Config

from app.config import Settings


class S3Storage:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
            config=Config(retries={"max_attempts": 4, "mode": "standard"}),
        )

    def download(self, key: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.logger.info("Baixando PDF do S3 key=%s", key)
        self.client.download_file(self.settings.s3_bucket, key, str(destination))

    def upload(self, source: Path, key: str) -> None:
        self.logger.info("Enviando PDF OCR para S3 key=%s", key)
        self.client.upload_file(str(source), self.settings.s3_bucket, key)
