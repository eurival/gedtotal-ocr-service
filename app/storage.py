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
        
        endpoint = settings.s3_endpoint
        if endpoint and not endpoint.startswith(("http://", "https://")):
            endpoint = f"https://{endpoint}"
            
        boto_config = Config(
            retries={"max_attempts": 4, "mode": "standard"},
            s3={"addressing_style": "path" if settings.s3_path_style else "virtual"}
        )
        
        client_kwargs = {
            "region_name": settings.s3_region,
            "config": boto_config,
            "verify": settings.s3_verify_ssl,
        }
        
        if settings.aws_access_key_id:
            client_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            client_kwargs["aws_session_token"] = settings.aws_session_token
            
        if endpoint:
            client_kwargs["endpoint_url"] = endpoint
            
        self.logger.info("Inicializando cliente S3 (S3-compatible=%s, endpoint=%s)", bool(endpoint), endpoint)
        self.client = boto3.client("s3", **client_kwargs)

    def _validate_prefix(self, key: str) -> None:
        if not key:
            raise ValueError("Chave S3 vazia ou invalida.")
        
        # Validacao de seguranca de caminhos
        if key.startswith("/"):
            self.logger.error("Acesso negado: chave S3 '%s' nao pode iniciar com '/'", key)
            raise ValueError(f"Acesso negado: chave S3 '{key}' nao pode iniciar com '/'")
            
        if "\\" in key:
            self.logger.error("Acesso negado: chave S3 '%s' nao pode conter '\\'", key)
            raise ValueError(f"Acesso negado: chave S3 '{key}' nao pode conter '\\'")
            
        # Rejeita segmentos de caminho exatamente iguais a '.' ou '..'
        segments = key.split("/")
        if any(seg in {".", ".."} for seg in segments):
            self.logger.error("Acesso negado: chave S3 '%s' contem segmentos relativos '.' ou '..'", key)
            raise ValueError(f"Acesso negado: chave S3 '{key}' contem segmentos relativos '.' ou '..'")
            
        prefix = self.settings.s3_allowed_prefix
        if prefix:
            # Normalizar o prefixo configurado para terminar com '/'
            normalized_prefix = prefix if prefix.endswith("/") else f"{prefix}/"
            if not key.startswith(normalized_prefix):
                self.logger.error("Acesso negado: chave S3 '%s' esta fora do prefixo permitido '%s'", key, normalized_prefix)
                raise ValueError(f"Acesso Folder: chave S3 '{key}' esta fora do prefixo permitido '{normalized_prefix}'")

    def download(self, key: str, destination: Path) -> None:
        self._validate_prefix(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.logger.info("Baixando PDF do S3 key=%s", key)
        self.client.download_file(self.settings.s3_bucket, key, str(destination))

    def upload(self, source: Path, key: str) -> None:
        self._validate_prefix(key)
        self.logger.info("Enviando PDF OCR para S3 key=%s", key)
        self.client.upload_file(str(source), self.settings.s3_bucket, key)
