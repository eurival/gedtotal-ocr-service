# -*- coding: utf-8 -*-
#
# Classe:
#    Settings
# Descrição:
#    Classe de configuração
# Autor:
#    Euríval
# Data:
#    2026-01-13
# Arquivo:
#    config.py
# Função:
#    Classe de configuração
# Importações:
#    from __future__ import annotations
#    import os
#    from dataclasses import dataclass


from dataclasses import dataclass


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    if value is None or not value.strip():
        return default
    return int(value)


@dataclass(frozen=True)
class Settings:
    app_name: str
    server_port: int
    kafka_bootstrap_servers: str
    kafka_input_topic: str
    kafka_output_topic: str
    kafka_failure_topic: str
    kafka_group_id: str
    kafka_auto_offset_reset: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    s3_bucket: str
    tmp_dir: str
    ocr_language: str
    ocr_jobs: int
    ocr_output_type: str
    ocr_force: bool
    ocr_rotate_pages: bool
    ocr_clean: bool
    ocr_optimize: int
    ocr_use_threads: bool
    overwrite_source: bool
    output_suffix: str
    log_level: str
    storage_provider: str
    s3_endpoint: str
    s3_region: str
    s3_path_style: bool
    s3_verify_ssl: bool
    s3_allowed_prefix: str
    aws_session_token: str

    @classmethod
    def from_env(cls) -> "Settings":
        import os
        required_vars = [
            "KAFKA_BOOTSTRAP_SERVERS",
            "KAFKA_INPUT_TOPIC",
            "KAFKA_OUTPUT_TOPIC",
            "KAFKA_FAILURE_TOPIC",
            "KAFKA_GROUP_ID",
            "S3_BUCKET",
        ]
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Variaveis de ambiente obrigatorias ausentes no startup: {', '.join(missing)}")

        # Validacao de credenciais em par e session token dependente
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        session_token = os.getenv("AWS_SESSION_TOKEN")

        if (access_key and not secret_key) or (secret_key and not access_key):
            raise ValueError("As credenciais AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY devem ser fornecidas em par (ambas preenchidas ou ambas ausentes).")

        if session_token and (not access_key or not secret_key):
            raise ValueError("A variavel AWS_SESSION_TOKEN nao pode ser fornecida sem o par AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY.")

        provider = os.getenv("STORAGE_PROVIDER", "s3")
        if provider.lower() != "s3":
            raise ValueError(f"STORAGE_PROVIDER '{provider}' nao e suportado. Atualmente apenas 's3' e implementado.")

        return cls(
            app_name=os.getenv("APP_NAME", "gedtotal-ocr-service"),
            server_port=_as_int(os.getenv("SERVER_PORT"), 8093),
            kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "15.229.173.87:19092"),
            kafka_input_topic=os.getenv("KAFKA_INPUT_TOPIC", "arquivos-processar-gedtotal-ocr"),
            kafka_output_topic=os.getenv("KAFKA_OUTPUT_TOPIC", "extrair-texto-pdf"),
            kafka_failure_topic=os.getenv("KAFKA_FAILURE_TOPIC", "arquivos-processar-gedtotal-ocr-falha"),
            kafka_group_id=os.getenv("KAFKA_GROUP_ID", "gedtotal-ocr-service"),
            kafka_auto_offset_reset=os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            aws_region=os.getenv("AWS_REGION", "sa-east-1"),
            s3_bucket=os.getenv("S3_BUCKET", "gedtotal"),
            tmp_dir=os.getenv("TMP_DIR", "/tmp/gedtotal-ocr"),
            ocr_language=os.getenv("OCR_LANGUAGE", "por"),
            ocr_jobs=_as_int(os.getenv("OCR_JOBS"), os.cpu_count() or 2),
            ocr_output_type=os.getenv("OCR_OUTPUT_TYPE", "pdfa"),
            ocr_force=_as_bool(os.getenv("OCR_FORCE"), True),
            ocr_rotate_pages=_as_bool(os.getenv("OCR_ROTATE_PAGES"), True),
            ocr_clean=_as_bool(os.getenv("OCR_CLEAN"), True),
            ocr_optimize=_as_int(os.getenv("OCR_OPTIMIZE"), 3),
            ocr_use_threads=_as_bool(os.getenv("OCR_USE_THREADS"), True),
            overwrite_source=_as_bool(os.getenv("OCR_OVERWRITE_SOURCE"), True),
            output_suffix=os.getenv("OCR_OUTPUT_SUFFIX", "-ocr"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            storage_provider=os.getenv("STORAGE_PROVIDER", "s3"),
            s3_endpoint=os.getenv("S3_ENDPOINT", ""),
            s3_region=os.getenv("S3_REGION") or os.getenv("AWS_REGION", "sa-east-1"),
            s3_path_style=_as_bool(os.getenv("S3_PATH_STYLE"), False),
            s3_verify_ssl=_as_bool(os.getenv("S3_VERIFY_SSL"), True),
            s3_allowed_prefix=os.getenv("S3_ALLOWED_PREFIX", ""),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN", ""),
        )
