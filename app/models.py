from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OCRRequestMessage:
    arquivo_id: int
    caminho_arquivo: str
    trace_id: str | None = None
    nome_arquivo: str | None = None
    nome_cliente: str | None = None
    cpfcnpj_cliente: str | None = None
    nome_departamento: str | None = None
    nome_projeto: str | None = None
    nome_formulario: str | None = None
    tipo_documental: str | None = None
    classificacao_conarq: str | None = None

    @classmethod
    def from_json(cls, payload: str) -> "OCRRequestMessage":
        data = json.loads(payload)
        return cls(
            arquivo_id=int(data["id"]),
            caminho_arquivo=data["caminhoarquivo"],
            trace_id=data.get("traceId"),
            nome_arquivo=data.get("nomeArquivo"),
            nome_cliente=data.get("nomeCliente"),
            cpfcnpj_cliente=data.get("cpfcnpjCliente"),
            nome_departamento=data.get("nomeDepartamento"),
            nome_projeto=data.get("nomeProjeto"),
            nome_formulario=data.get("nomeFormulario"),
            tipo_documental=data.get("tipoDocumental"),
            classificacao_conarq=data.get("classificacaoConarq"),
        )


@dataclass(frozen=True)
class OCRResultMessage:
    arquivo_id: int
    caminho_arquivo: str
    ocr_applied: bool
    trace_id: str | None
    hash_sha256: str | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "id": self.arquivo_id,
                "caminhoarquivo": self.caminho_arquivo,
                "ocrApplied": self.ocr_applied,
                "traceId": self.trace_id,
                "hashSha256": self.hash_sha256,
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

