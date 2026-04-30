from __future__ import annotations

import logging
import shutil
import threading
from pathlib import Path

from confluent_kafka import Consumer, KafkaException

from app.config import Settings
from app.models import OCRFailureMessage, OCRRequestMessage, OCRResultMessage
from app.ocr_service import OCRService
from app.publisher import OCRPublisher
from app.storage import S3Storage


class OCRConsumer(threading.Thread):
    def __init__(self, settings: Settings):
        super().__init__(name="ocr-consumer", daemon=True)
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)
        self.consumer = Consumer(
            {
                "bootstrap.servers": settings.kafka_bootstrap_servers,
                "group.id": settings.kafka_group_id,
                "auto.offset.reset": settings.kafka_auto_offset_reset,
                "enable.auto.commit": False,
                "max.poll.interval.ms": 1800000,  # 30min — PDFs grandes (600+ pg) podem demorar
            }
        )
        self.storage = S3Storage(settings)
        self.ocr_service = OCRService(settings)
        self.publisher = OCRPublisher(settings)
        self.ready = False
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()
        try:
            self.consumer.close()
        except Exception:
            self.logger.exception("Falha ao fechar consumer Kafka")

    def run(self) -> None:
        self.consumer.subscribe([self.settings.kafka_input_topic])
        self.ready = True
        self.logger.info("Consumer OCR ouvindo topico=%s groupId=%s", self.settings.kafka_input_topic, self.settings.kafka_group_id)
        while not self._stop_event.is_set():
            msg = self.consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                self.logger.error("Erro no Kafka consumer: %s", msg.error())
                continue
            self._handle_message(msg.value().decode("utf-8"))
            self.consumer.commit(message=msg)

    def _handle_message(self, payload: str) -> None:
        request = OCRRequestMessage.from_json(payload)
        work_dir = Path(self.settings.tmp_dir) / str(request.arquivo_id)
        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
        input_path = work_dir / "input.pdf"
        output_path = work_dir / "output.pdf"
        try:
            self.storage.download(request.caminho_arquivo, input_path)
            ocr_applied, output_key, hash_sha256 = self.ocr_service.process(request, input_path, output_path)
            self.storage.upload(output_path, output_key)
            self.publisher.publish_result(
                OCRResultMessage(
                    arquivo_id=request.arquivo_id,
                    caminho_arquivo=output_key,
                    ocr_applied=ocr_applied,
                    trace_id=request.trace_id,
                    hash_sha256=hash_sha256,
                )
            )
        except Exception as exc:
            self.logger.exception("Falha no OCR arquivoId=%s key=%s", request.arquivo_id, request.caminho_arquivo)
            self.publisher.publish_failure(
                OCRFailureMessage(
                    arquivo_id=request.arquivo_id,
                    caminho_arquivo=request.caminho_arquivo,
                    error_code="OCR_JOB_ERROR",
                    error_message=str(exc),
                    trace_id=request.trace_id,
                )
            )
        finally:
            if work_dir.exists():
                shutil.rmtree(work_dir, ignore_errors=True)
                self.logger.debug("Diretorio temporario removido %s", work_dir)


def ensure_kafka_available(settings: Settings) -> None:
    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": f"{settings.kafka_group_id}-healthcheck",
            "session.timeout.ms": 6000,
        }
    )
    try:
        metadata = consumer.list_topics(timeout=10)
        if metadata.orig_broker_name is None:
            raise KafkaException("Kafka metadata indisponivel")
    finally:
        consumer.close()
