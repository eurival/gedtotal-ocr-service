# -*- coding: utf-8 -*-
from pathlib import Path
import pytest
from unittest import mock
from app.config import Settings
from app.storage import S3Storage


@pytest.fixture
def base_settings():
    return Settings(
        app_name="gedtotal-ocr-service",
        server_port=8093,
        kafka_bootstrap_servers="localhost:9092",
        kafka_input_topic="input-topic",
        kafka_output_topic="output-topic",
        kafka_failure_topic="failure-topic",
        kafka_group_id="group-id",
        kafka_auto_offset_reset="earliest",
        aws_access_key_id="",
        aws_secret_access_key="",
        aws_region="sa-east-1",
        s3_bucket="gedtotal",
        tmp_dir="/tmp/gedtotal-ocr",
        ocr_language="por",
        ocr_jobs=2,
        ocr_output_type="pdfa",
        ocr_force=True,
        ocr_rotate_pages=True,
        ocr_clean=True,
        ocr_optimize=3,
        ocr_use_threads=True,
        overwrite_source=True,
        output_suffix="-ocr",
        log_level="INFO",
        storage_provider="s3",
        s3_endpoint="",
        s3_region="sa-east-1",
        s3_path_style=False,
        s3_verify_ssl=True,
        s3_allowed_prefix="",
        aws_session_token="",
    )


@mock.patch("app.storage.boto3.client")
def test_storage_client_config_aws_official(mock_boto_client, base_settings):
    # AWS Oficial
    settings = base_settings
    S3Storage(settings)
    
    mock_boto_client.assert_called_once()
    args, kwargs = mock_boto_client.call_args
    assert args[0] == "s3"
    assert kwargs["region_name"] == "sa-east-1"
    assert "endpoint_url" not in kwargs
    assert kwargs["verify"] is True
    assert kwargs["config"].s3["addressing_style"] == "virtual"
    assert "aws_access_key_id" not in kwargs


@mock.patch("app.storage.boto3.client")
def test_storage_client_config_eveo(mock_boto_client, base_settings):
    # EVEO S3-compatible com endpoint customizado, regiao auto, path style, session token
    settings = Settings(
        **{
            **base_settings.__dict__,
            "s3_endpoint": "object.sp2.eveo.com.br",
            "s3_region": "auto",
            "s3_path_style": True,
            "s3_verify_ssl": True,
            "aws_access_key_id": "AKIA123",
            "aws_secret_access_key": "secret123",
            "aws_session_token": "session123",
        }
    )
    S3Storage(settings)
    
    mock_boto_client.assert_called_once()
    args, kwargs = mock_boto_client.call_args
    assert args[0] == "s3"
    assert kwargs["region_name"] == "auto"
    assert kwargs["endpoint_url"] == "https://object.sp2.eveo.com.br"
    assert kwargs["verify"] is True
    assert kwargs["config"].s3["addressing_style"] == "path"
    assert kwargs["aws_access_key_id"] == "AKIA123"
    assert kwargs["aws_secret_access_key"] == "secret123"
    assert kwargs["aws_session_token"] == "session123"


@mock.patch("app.storage.boto3.client")
def test_storage_client_endpoint_url_protocol_preservation(mock_boto_client, base_settings):
    # Endpoint ja contem protocolo
    settings = Settings(
        **{
            **base_settings.__dict__,
            "s3_endpoint": "https://object.sp2.eveo.com.br",
        }
    )
    S3Storage(settings)
    
    mock_boto_client.assert_called_once()
    args, kwargs = mock_boto_client.call_args
    assert kwargs["endpoint_url"] == "https://object.sp2.eveo.com.br"


def test_storage_prefix_validation_valid(base_settings):
    settings = base_settings
    storage = S3Storage(settings)
    
    # Validos
    storage._validate_prefix("documentos/1/empresas/1/arquivo.pdf")
    storage._validate_prefix("documentos/relatorio..final.pdf")
    storage._validate_prefix("licitai/ocr/licitacoes/10/arquivos/20/original.pdf")


def test_storage_prefix_validation_invalid(base_settings):
    settings = base_settings
    storage = S3Storage(settings)
    
    # Invalidos
    invalid_keys = [
        "",
        "/",
        "\\arquivo.pdf",
        "../arquivo.pdf",
        "documentos/../segredo.pdf",
        "documentos/./arquivo.pdf",
        "/outro/arquivo.pdf",
    ]
    for key in invalid_keys:
        with pytest.raises(ValueError):
            storage._validate_prefix(key)


def test_storage_prefix_allowed_restriction(base_settings):
    # Testando prefixo restrito
    settings = Settings(
        **{
            **base_settings.__dict__,
            "s3_allowed_prefix": "documentos/",
        }
    )
    storage = S3Storage(settings)
    
    # Aceita
    storage._validate_prefix("documentos/arquivo.pdf")
    
    # Rejeita
    with pytest.raises(ValueError):
        storage._validate_prefix("documentos-maliciosos/arquivo.pdf")
    with pytest.raises(ValueError):
        storage._validate_prefix("outro/arquivo.pdf")


@mock.patch("app.storage.boto3.client")
def test_storage_download_upload(mock_boto_client, base_settings):
    mock_s3 = mock.MagicMock()
    mock_boto_client.return_value = mock_s3
    
    settings = base_settings
    storage = S3Storage(settings)
    
    # Download
    dest = Path("/tmp/test-dest.pdf")
    storage.download("documentos/arquivo.pdf", dest)
    mock_s3.download_file.assert_called_once_with("gedtotal", "documentos/arquivo.pdf", str(dest))
    
    # Upload
    source = Path("/tmp/test-source.pdf")
    storage.upload(source, "documentos/output-ocr.pdf")
    mock_s3.upload_file.assert_called_once_with(str(source), "gedtotal", "documentos/output-ocr.pdf")


@mock.patch("app.storage.boto3.client")
def test_storage_invalid_key_never_hits_boto(mock_boto_client, base_settings):
    mock_s3 = mock.MagicMock()
    mock_boto_client.return_value = mock_s3
    
    settings = base_settings
    storage = S3Storage(settings)
    
    # Download chave invalida
    dest = Path("/tmp/test-dest.pdf")
    with pytest.raises(ValueError):
        storage.download("../invalido.pdf", dest)
    
    mock_s3.download_file.assert_not_called()
