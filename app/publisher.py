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

    def publish_result(self, message: OCRResultMessage) -> None:
        payload = message.to_json()
        self.logger.info("Publicando resultado OCR arquivoId=%s topico=%s", message.arquivo_id, self.settings.kafka_output_topic)
        self.producer.produce(self.settings.kafka_output_topic, key=str(message.arquivo_id), value=payload)
        self.producer.flush()

    def publish_failure(self, message: OCRFailureMessage) -> None:
        payload = message.to_json()
        self.logger.error("Publicando falha OCR arquivoId=%s topico=%s code=%s", message.arquivo_id, self.settings.kafka_failure_topic, message.error_code)
        self.producer.produce(self.settings.kafka_failure_topic, key=str(message.arquivo_id), value=payload)
        self.producer.flush()
