from __future__ import annotations

import logging

from confluent_kafka import Producer

from app.config import Settings
from app.models import OCRFailureMessage, OCRResultMessage


class OCRPublisher:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)
        self.producer = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})

    def publish_result(self, message: OCRResultMessage, topic: str | None = None) -> None:
        payload = message.to_json()
        target_topic = topic or self.settings.kafka_output_topic
        self.logger.info("Publicando resultado OCR arquivoId=%s topico=%s", message.arquivo_id, target_topic)
        self.producer.produce(target_topic, key=str(message.arquivo_id), value=payload)
        self.producer.flush()

    def publish_failure(self, message: OCRFailureMessage, topic: str | None = None) -> None:
        payload = message.to_json()
        target_topic = topic or self.settings.kafka_failure_topic
        self.logger.error("Publicando falha OCR arquivoId=%s topico=%s code=%s", message.arquivo_id, target_topic, message.error_code)
        self.producer.produce(target_topic, key=str(message.arquivo_id), value=payload)
        self.producer.flush()
