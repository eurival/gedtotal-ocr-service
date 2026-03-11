# gedtotal-ocr-service

Microservico Python responsavel por aplicar OCR em PDFs publicados no S3 a partir de comandos Kafka.

## Responsabilidade
- consumir pedidos de OCR no Kafka
- baixar PDF do S3
- aplicar OCR com `ocrmypdf`
- reenviar o PDF ao S3
- publicar resultado ou falha no Kafka

## Topicos padrao
- entrada: `arquivos-processar-gedtotal-ocr`
- saida: `extrair-texto-pdf`
- falha: `arquivos-processar-gedtotal-ocr-falha`

## Variaveis principais
- `KAFKA_BOOTSTRAP_SERVERS`
- `KAFKA_INPUT_TOPIC`
- `KAFKA_OUTPUT_TOPIC`
- `KAFKA_FAILURE_TOPIC`
- `KAFKA_GROUP_ID`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `S3_BUCKET`
- `OCR_LANGUAGE`
- `OCR_JOBS`
- `OCR_OUTPUT_TYPE`
- `OCR_FORCE`
- `OCR_OVERWRITE_SOURCE`
- `OCR_OUTPUT_SUFFIX`

## Execucao local
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

## Endpoints
- `GET /actuator/health`
- `GET /actuator/health/liveness`
- `GET /actuator/health/readiness`

## Comportamento atual
Por compatibilidade com o script legado, o servico sobrescreve o mesmo objeto no S3 por padrao.
Defina `OCR_OVERWRITE_SOURCE=false` para gerar uma variante com sufixo.
