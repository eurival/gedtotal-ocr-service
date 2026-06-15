# -*- coding: utf-8 -*-
import os
import sys
from unittest import mock
import pytest


def test_main_bootstrap_imports(monkeypatch):
    """
    Testa se o módulo app.main pode ser importado com sucesso (bootstrap)
    sem levantar erros de NameError por imports ausentes (como logging, signal, sys).
    O teste fornece as variáveis obrigatórias e isola chamadas de rede/banco/clientes.
    """
    # 1. Fornecer variáveis de ambiente obrigatórias
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    monkeypatch.setenv("KAFKA_INPUT_TOPIC", "input-topic")
    monkeypatch.setenv("KAFKA_OUTPUT_TOPIC", "output-topic")
    monkeypatch.setenv("KAFKA_FAILURE_TOPIC", "failure-topic")
    monkeypatch.setenv("KAFKA_GROUP_ID", "group-id")
    monkeypatch.setenv("S3_BUCKET", "gedtotal-test-bucket")
    monkeypatch.setenv("TMP_DIR", "/tmp/gedtotal-test-bootstrap")

    # 2. Mockar as dependências pesadas externas
    with mock.patch("app.consumer.Consumer") as mock_consumer, \
         mock.patch("app.storage.boto3.client") as mock_boto_client:
        
        # 3. Forçar o recarregamento do módulo app.main se ele já tiver sido importado
        if "app.main" in sys.modules:
            del sys.modules["app.main"]

        # 4. Importar o módulo app.main
        import app.main

        # 5. Assegurar que as variáveis globais críticas foram instanciadas
        assert app.main.app is not None
        assert app.main.consumer is not None
        
        # Garante que os mocks foram chamados
        assert mock_consumer.called
        assert mock_boto_client.called
