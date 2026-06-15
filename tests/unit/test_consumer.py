# -*- coding: utf-8 -*-
from pathlib import Path
import pytest
from unittest import mock
from app.config import Settings
from app.consumer import OCRConsumer
from app.models import OCRRequestMessage


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


@mock.patch("app.consumer.Consumer")
@mock.patch("app.consumer.S3Storage")
@mock.patch("app.consumer.OCRService")
@mock.patch("app.consumer.OCRPublisher")
def test_consumer_successful_flow(
    mock_publisher_cls,
    mock_ocr_service_cls,
    mock_storage_cls,
    mock_consumer_cls,
    base_settings,
):
    # Setup mocks
    mock_consumer = mock.MagicMock()
    mock_consumer_cls.return_value = mock_consumer
    
    mock_storage = mock.MagicMock()
    mock_storage_cls.return_value = mock_storage
    
    mock_ocr_service = mock.MagicMock()
    mock_ocr_service_cls.return_value = mock_ocr_service
    mock_ocr_service.process.return_value = (True, "documentos/output-ocr.pdf", "hash123")
    
    mock_publisher = mock.MagicMock()
    mock_publisher_cls.return_value = mock_publisher

    # Instancia o consumer
    consumer_thread = OCRConsumer(base_settings)
    
    # Simula mensagem do Kafka
    payload = {
        "id": 9198398,
        "caminhoarquivo": "documentos/original.pdf",
        "traceId": "trace-123",
        "sourceSystem": "LICITAI",
        "tenant": "1",
        "callbackTopic": "custom.success.topic",
        "failureTopic": "custom.failure.topic",
        "outputMode": "NEW_OBJECT",
        "outputSuffix": "-ocr"
    }
    
    # Mock do poll retornando uma mensagem
    mock_msg = mock.MagicMock()
    mock_msg.error.return_value = None
    mock_msg.value.return_value = str(payload).replace("'", '"').encode("utf-8")
    
    # Executa _handle_message diretamente
    consumer_thread._handle_message(mock_msg.value().decode("utf-8"))
    
    # Verifica download
    mock_storage.download.assert_called_once_with("documentos/original.pdf", mock.ANY)
    
    # Verifica ocr_service process
    mock_ocr_service.process.assert_called_once()
    
    # Verifica upload
    mock_storage.upload.assert_called_once_with(mock.ANY, "documentos/output-ocr.pdf")
    
    # Verifica publicacao de resultado
    mock_publisher.publish_result.assert_called_once()
    args, kwargs = mock_publisher.publish_result.call_args
    assert args[0].arquivo_id == 9198398
    assert args[0].caminho_arquivo == "documentos/output-ocr.pdf"
    assert kwargs["topic"] == "custom.success.topic"
    
    # Verifica que a falha nao foi publicada
    mock_publisher.publish_failure.assert_not_called()


@mock.patch("app.consumer.Consumer")
@mock.patch("app.consumer.S3Storage")
@mock.patch("app.consumer.OCRService")
@mock.patch("app.consumer.OCRPublisher")
def test_consumer_failure_flow_during_ocr(
    mock_publisher_cls,
    mock_ocr_service_cls,
    mock_storage_cls,
    mock_consumer_cls,
    base_settings,
):
    mock_consumer = mock.MagicMock()
    mock_consumer_cls.return_value = mock_consumer
    
    mock_storage = mock.MagicMock()
    mock_storage.download.side_effect = Exception("S3 Download Error")
    mock_storage_cls.return_value = mock_storage
    
    mock_publisher = mock.MagicMock()
    mock_publisher_cls.return_value = mock_publisher

    consumer_thread = OCRConsumer(base_settings)
    
    payload = {
        "id": 9198398,
        "caminhoarquivo": "documentos/original.pdf",
        "traceId": "trace-123",
        "callbackTopic": "custom.success.topic",
        "failureTopic": "custom.failure.topic",
    }
    
    consumer_thread._handle_message(str(payload).replace("'", '"'))
    
    # Como o download falhou, a publicacao de falha deve ser chamada
    mock_publisher.publish_failure.assert_called_once()
    args, kwargs = mock_publisher.publish_failure.call_args
    assert args[0].arquivo_id == 9198398
    assert args[0].error_code == "OCR_JOB_ERROR"
    assert "S3 Download Error" in args[0].error_message
    assert kwargs["topic"] == "custom.failure.topic"
    
    # Nao publica resultado
    mock_publisher.publish_result.assert_not_called()


@mock.patch("app.consumer.Consumer")
@mock.patch("app.consumer.S3Storage")
@mock.patch("app.consumer.OCRService")
@mock.patch("app.consumer.OCRPublisher")
def test_consumer_broker_offline_no_commit(
    mock_publisher_cls,
    mock_ocr_service_cls,
    mock_storage_cls,
    mock_consumer_cls,
    base_settings,
):
    # Se a publicacao de sucesso e a de falha falharem, o erro se propaga e nao ha commit
    mock_consumer = mock.MagicMock()
    mock_consumer_cls.return_value = mock_consumer
    
    mock_storage = mock.MagicMock()
    mock_storage_cls.return_value = mock_storage
    
    mock_ocr_service = mock.MagicMock()
    mock_ocr_service_cls.return_value = mock_ocr_service
    mock_ocr_service.process.return_value = (True, "documentos/output-ocr.pdf", "hash123")
    
    mock_publisher = mock.MagicMock()
    mock_publisher.publish_result.side_effect = Exception("Kafka Broker Offline")
    mock_publisher.publish_failure.side_effect = Exception("Kafka Broker Offline")
    mock_publisher_cls.return_value = mock_publisher

    consumer_thread = OCRConsumer(base_settings)
    
    payload = {
        "id": 9198398,
        "caminhoarquivo": "documentos/original.pdf",
        "callbackTopic": "custom.success.topic",
        "failureTopic": "custom.failure.topic",
    }
    
    # _handle_message deve propagar o erro de broker offline ja que a falha tambem nao pode ser publicada
    with pytest.raises(Exception) as exc:
        consumer_thread._handle_message(str(payload).replace("'", '"'))
    
    assert "Kafka Broker Offline" in str(exc.value)
