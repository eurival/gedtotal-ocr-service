from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OCRRequestMessage:
    arquivo_id: int
    caminho_arquivo: str
    trace_id: str | None = None

    @classmethod
    def from_json(cls, payload: str) -> "OCRRequestMessage":
        data = json.loads(payload)
        return cls(
            arquivo_id=int(data["id"]),
            caminho_arquivo=data["caminhoarquivo"],
            trace_id=data.get("traceId"),
        )


@dataclass(frozen=True)
class OCRResultMessage:
    arquivo_id: int
    caminho_arquivo: str
    ocr_applied: bool
    trace_id: str | None

    def to_json(self) -> str:
        return json.dumps(
            {
                "id": self.arquivo_id,
                "caminhoarquivo": self.caminho_arquivo,
                "ocrApplied": self.ocr_applied,
                "traceId": self.trace_id,
            }
        )


@dataclass(frozen=True)
class OCRFailureMessage:
    arquivo_id: int
    caminho_arquivo: str
    error_code: str
    error_message: str
    trace_id: str | None

    def to_json(self) -> str:
        return json.dumps(
            {
                "id": self.arquivo_id,
                "caminhoarquivo": self.caminho_arquivo,
                "errorCode": self.error_code,
                "errorMessage": self.error_message,
                "traceId": self.trace_id,
            }
        )
