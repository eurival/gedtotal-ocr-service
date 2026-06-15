# -*- coding: utf-8 -*-
import uuid
from pathlib import Path
import pytest
import boto3
from app.config import Settings
from app.storage import S3Storage

pytestmark = pytest.mark.integration

MINIO_IMAGE = "minio/minio:RELEASE.2024-01-28T22-35-53Z"


@pytest.fixture(scope="module")
def minio_settings():
    container = None
    last_exception = None
    
    # 1. Tenta inicializar o MinIO via Testcontainers de forma exclusiva (sem fallback silencioso)
    try:
        from testcontainers.core.container import DockerContainer
        container = (
            DockerContainer(MINIO_IMAGE)
            .with_exposed_ports(9000)
            .with_command("server /data")
            .with_env("MINIO_ROOT_USER", "minioadmin")
            .with_env("MINIO_ROOT_PASSWORD", "minioadmin")
        )
        container.start()
        port = container.get_exposed_port(9000)
        host = container.get_container_host_ip()
        minio_endpoint = f"http://{host}:{port}"
    except Exception as exc:
        last_exception = exc

    # Se a inicializacao do Testcontainers falhar, pula o teste indicando a causa real
    if last_exception:
        pytest.skip(
            "Não foi possível iniciar o MinIO com Testcontainers: "
            f"{type(last_exception).__name__}: {last_exception}"
        )

    # 2. Cria o bucket unico gerado com UUID
    bucket_name = f"gedtotal-it-{uuid.uuid4().hex}"
    
    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=minio_endpoint,
            aws_access_key_id="minioadmin",
            aws_secret_access_key="minioadmin",
            region_name="us-east-1",
        )
        s3_client.create_bucket(Bucket=bucket_name)
    except Exception as exc:
        # Se falhar a criacao do bucket local, precisamos finalizar o container antes de falhar
        if container:
            try:
                container.stop()
            except Exception:
                pass
        raise exc

    settings = Settings(
        app_name="gedtotal-ocr-service-integration",
        server_port=8093,
        kafka_bootstrap_servers="localhost:9092",
        kafka_input_topic="input-topic",
        kafka_output_topic="output-topic",
        kafka_failure_topic="failure-topic",
        kafka_group_id="group-id",
        kafka_auto_offset_reset="earliest",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        aws_region="us-east-1",
        s3_bucket=bucket_name,
        tmp_dir="/tmp/gedtotal-ocr-integration",
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
        s3_endpoint=minio_endpoint,
        s3_region="us-east-1",
        s3_path_style=True,
        s3_verify_ssl=False,
        s3_allowed_prefix="documentos/",
        aws_session_token="",
    )

    try:
        yield settings
    finally:
        # 3. Cleanup obrigatorio no bloco finally
        # Garante a remocao de objetos e do bucket descartavel
        try:
            objects = s3_client.list_objects_v2(Bucket=bucket_name)
            if "Contents" in objects:
                for obj in objects["Contents"]:
                    s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])
            s3_client.delete_bucket(Bucket=bucket_name)
        except Exception:
            pass

        # Garante o encerramento do container em qualquer cenario
        if container:
            try:
                container.stop()
            except Exception:
                pass


def test_s3_storage_integration_flow(minio_settings, tmp_path):
    storage = S3Storage(minio_settings)

    # 4. Arquivos temporarios isolados com tmp_path
    local_source = tmp_path / "test_integration_input.pdf"
    local_source.write_bytes(b"%PDF-1.4 Fake PDF Content for Integration Test")

    key = "documentos/1/empresas/1/contrato.pdf"
    
    # Upload do arquivo
    storage.upload(local_source, key)

    # Download do arquivo e comparacao
    local_dest = tmp_path / "test_integration_output.pdf"
    storage.download(key, local_dest)

    assert local_dest.exists()
    assert local_dest.read_bytes() == local_source.read_bytes()

    # Validacao de prefixo invalido
    with pytest.raises(ValueError):
        storage.upload(local_source, "outra-pasta/arquivo.pdf")
