# -*- coding: utf-8 -*-
import os
import pytest
from unittest import mock
from app.config import Settings


def test_settings_default_required_missing():
    # Deve falhar se variaveis requeridas estiverem ausentes
    with mock.patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError) as exc:
            Settings.from_env()
        assert "Variaveis de ambiente obrigatorias ausentes" in str(exc.value)


@pytest.fixture
def base_env():
    return {
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
        "KAFKA_INPUT_TOPIC": "input-topic",
        "KAFKA_OUTPUT_TOPIC": "output-topic",
        "KAFKA_FAILURE_TOPIC": "failure-topic",
        "KAFKA_GROUP_ID": "group-id",
        "S3_BUCKET": "gedtotal",
    }


def test_settings_region_priorities(base_env):
    # S3_REGION definida -> vence AWS_REGION
    env = {**base_env, "S3_REGION": "us-west-2", "AWS_REGION": "sa-east-1"}
    with mock.patch.dict(os.environ, env, clear=True):
        settings = Settings.from_env()
        assert settings.s3_region == "us-west-2"

    # S3_REGION ausente + AWS_REGION definida -> usa AWS_REGION
    env = {**base_env, "AWS_REGION": "us-east-1"}
    if "S3_REGION" in env:
        del env["S3_REGION"]
    with mock.patch.dict(os.environ, env, clear=True):
        settings = Settings.from_env()
        assert settings.s3_region == "us-east-1"

    # ambas ausentes -> usa sa-east-1
    env = base_env.copy()
    if "S3_REGION" in env:
        del env["S3_REGION"]
    if "AWS_REGION" in env:
        del env["AWS_REGION"]
    with mock.patch.dict(os.environ, env, clear=True):
        settings = Settings.from_env()
        assert settings.s3_region == "sa-east-1"

    # S3_REGION=auto -> mantém literalmente "auto"
    env = {**base_env, "S3_REGION": "auto"}
    with mock.patch.dict(os.environ, env, clear=True):
        settings = Settings.from_env()
        assert settings.s3_region == "auto"


def test_settings_provider_validation(base_env):
    # STORAGE_PROVIDER=s3 -> valido
    env = {**base_env, "STORAGE_PROVIDER": "s3"}
    with mock.patch.dict(os.environ, env, clear=True):
        settings = Settings.from_env()
        assert settings.storage_provider == "s3"

    # STORAGE_PROVIDER=local -> falha claramente
    env = {**base_env, "STORAGE_PROVIDER": "local"}
    with mock.patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValueError) as exc:
            Settings.from_env()
        assert "nao e suportado" in str(exc.value)

    # STORAGE_PROVIDER desconhecido -> falha claramente
    env = {**base_env, "STORAGE_PROVIDER": "unknown"}
    with mock.patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValueError) as exc:
            Settings.from_env()
        assert "nao e suportado" in str(exc.value)


def test_settings_credentials_pairs(base_env):
    # nenhuma credencial explicita -> permitido (chain fallback)
    env = base_env.copy()
    if "AWS_ACCESS_KEY_ID" in env:
        del env["AWS_ACCESS_KEY_ID"]
    if "AWS_SECRET_ACCESS_KEY" in env:
        del env["AWS_SECRET_ACCESS_KEY"]
    with mock.patch.dict(os.environ, env, clear=True):
        settings = Settings.from_env()
        assert settings.aws_access_key_id == ""
        assert settings.aws_secret_access_key == ""

    # access key sem secret -> invalido
    env = {**base_env, "AWS_ACCESS_KEY_ID": "AKIA123"}
    if "AWS_SECRET_ACCESS_KEY" in env:
        del env["AWS_SECRET_ACCESS_KEY"]
    with mock.patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValueError) as exc:
            Settings.from_env()
        assert "devem ser fornecidas em par" in str(exc.value)

    # secret sem access key -> invalido
    env = {**base_env, "AWS_SECRET_ACCESS_KEY": "secret123"}
    if "AWS_ACCESS_KEY_ID" in env:
        del env["AWS_ACCESS_KEY_ID"]
    with mock.patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValueError) as exc:
            Settings.from_env()
        assert "devem ser fornecidas em par" in str(exc.value)

    # access + secret -> valido
    env = {**base_env, "AWS_ACCESS_KEY_ID": "AKIA123", "AWS_SECRET_ACCESS_KEY": "secret123"}
    with mock.patch.dict(os.environ, env, clear=True):
        settings = Settings.from_env()
        assert settings.aws_access_key_id == "AKIA123"
        assert settings.aws_secret_access_key == "secret123"


def test_settings_session_token_dependency(base_env):
    # session token sem as chaves em par -> invalido
    env = {**base_env, "AWS_SESSION_TOKEN": "token123"}
    if "AWS_ACCESS_KEY_ID" in env:
        del env["AWS_ACCESS_KEY_ID"]
    if "AWS_SECRET_ACCESS_KEY" in env:
        del env["AWS_SECRET_ACCESS_KEY"]
    with mock.patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValueError) as exc:
            Settings.from_env()
        assert "AWS_SESSION_TOKEN nao pode ser fornecida sem o par" in str(exc.value)

    # session token com as chaves em par -> valido
    env = {
        **base_env,
        "AWS_ACCESS_KEY_ID": "AKIA123",
        "AWS_SECRET_ACCESS_KEY": "secret123",
        "AWS_SESSION_TOKEN": "token123",
    }
    with mock.patch.dict(os.environ, env, clear=True):
        settings = Settings.from_env()
        assert settings.aws_session_token == "token123"
