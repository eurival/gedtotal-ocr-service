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

## Modo LicitAI

Para reutilizar este worker no LicitAI sem misturar os fluxos do GedTotal, suba uma instancia separada com topicos e bucket proprios:

```bash
APP_NAME=licitai-ocr-service
KAFKA_BOOTSTRAP_SERVERS=15.229.173.87:19092
KAFKA_INPUT_TOPIC=licitai.ocr.requests
KAFKA_OUTPUT_TOPIC=licitai.ocr.results
KAFKA_FAILURE_TOPIC=licitai.ocr.failures
KAFKA_GROUP_ID=licitai-ocr-service
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=sa-east-1
S3_BUCKET=licitai-ai-processing
OCR_OVERWRITE_SOURCE=false
OCR_OUTPUT_SUFFIX=-ocr
```

O payload LicitAI mantem compatibilidade com o formato legado e adiciona metadados opcionais:

```json
{
  "id": 3329460,
  "caminhoarquivo": "licitai/ocr/licitacoes/152978/arquivos/3329460/original.pdf",
  "traceId": "licitai-ocr-152978-3329460-ab12cd34",
  "sourceSystem": "LICITAI",
  "tenant": "licitai",
  "licitacaoId": 152978,
  "arquivoLicitacaoId": 3329460,
  "nomeArquivo": "EDITAL.pdf",
  "callbackTopic": "licitai.ocr.results",
  "failureTopic": "licitai.ocr.failures",
  "outputMode": "NEW_OBJECT",
  "outputSuffix": "-ocr"
}
```

As credenciais S3 nao devem vir no payload. Elas continuam no ambiente/secret do servico.

### PDFs assinados digitalmente no LicitAI

Quando o payload define `outputMode=NEW_OBJECT`, o servico pode executar OCR em PDF assinado usando uma copia derivada. A assinatura digital do output OCR sera invalidada, mas o PDF original no S3 permanece intacto.

Regra implementada:

- `outputMode=NEW_OBJECT`: permite `invalidate_digital_signatures=True`, pois o resultado e artefato derivado apenas para extracao/indexacao de texto.
- overwrite do objeto original: nao invalida assinatura; se o PDF for assinado, o OCR e pulado e o original e preservado.

O LicitAI deve usar sempre:

```json
{
  "outputMode": "NEW_OBJECT",
  "outputSuffix": "-ocr"
}
```
