# -*- coding: utf-8 -*-
import json
from app.models import OCRRequestMessage, OCRResultMessage, OCRFailureMessage


def test_ocr_request_message_parsing():
    payload = json.dumps(
        {
            "id": 9198398,
            "caminhoarquivo": "documentos/1/empresas/1/9198398/original.pdf",
            "traceId": "trace-123",
            "sourceSystem": "LICITAI",
            "tenant": "1",
            "callbackTopic": "licitai.documento.ocr.processado",
            "failureTopic": "licitai.documento.ocr.falhou",
            "outputMode": "NEW_OBJECT",
            "outputSuffix": "-ocr",
            "licitacaoId": 12,
            "arquivoLicitacaoId": 34,
            "nomeArquivo": "original.pdf"
        }
    )
    
    msg = OCRRequestMessage.from_json(payload)
    
    assert msg.arquivo_id == 9198398
    assert msg.caminho_arquivo == "documentos/1/empresas/1/9198398/original.pdf"
    assert msg.trace_id == "trace-123"
    assert msg.source_system == "LICITAI"
    assert msg.tenant == "1"
    assert msg.callback_topic == "licitai.documento.ocr.processado"
    assert msg.failure_topic == "licitai.documento.ocr.falhou"
    assert msg.output_mode == "NEW_OBJECT"
    assert msg.output_suffix == "-ocr"
    assert msg.licitacao_id == 12
    assert msg.arquivo_licitacao_id == 34
    assert msg.nome_arquivo == "original.pdf"


def test_ocr_result_message_serialization():
    msg = OCRResultMessage(
        arquivo_id=9198398,
        caminho_arquivo="documentos/1/empresas/1/9198398/original-ocr.pdf",
        ocr_applied=True,
        trace_id="trace-123",
        hash_sha256="abc123hash",
        source_system="LICITAI",
        tenant="1",
        licitacao_id=12,
        arquivo_licitacao_id=None,  # Deve ser descartado no JSON
    )
    
    serialized_str = msg.to_json()
    data = json.loads(serialized_str)
    
    assert data["id"] == 9198398
    assert data["caminhoarquivo"] == "documentos/1/empresas/1/9198398/original-ocr.pdf"
    assert data["ocrApplied"] is True
    assert data["traceId"] == "trace-123"
    assert data["hashSha256"] == "abc123hash"
    assert data["sourceSystem"] == "LICITAI"
    assert data["tenant"] == "1"
    assert data["licitacaoId"] == 12
    assert "arquivoLicitacaoId" not in data


def test_ocr_failure_message_serialization():
    msg = OCRFailureMessage(
        arquivo_id=9198398,
        caminho_arquivo="documentos/1/empresas/1/9198398/original.pdf",
        error_code="OCR_JOB_ERROR",
        error_message="Falha de teste",
        trace_id="trace-123",
        source_system="LICITAI",
        tenant="1",
        licitacao_id=None,
        arquivo_licitacao_id=None,
    )
    
    serialized_str = msg.to_json()
    data = json.loads(serialized_str)
    
    assert data["id"] == 9198398
    assert data["caminhoarquivo"] == "documentos/1/empresas/1/9198398/original.pdf"
    assert data["errorCode"] == "OCR_JOB_ERROR"
    assert data["errorMessage"] == "Falha de teste"
    assert data["traceId"] == "trace-123"
    assert data["sourceSystem"] == "LICITAI"
    assert data["tenant"] == "1"
    assert "licitacaoId" not in data
    assert "arquivoLicitacaoId" not in data
