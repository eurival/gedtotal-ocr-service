# Arquitetura do Serviço Compartilhado de OCR

## 1. Visão Geral
O `gedtotal-ocr-service` é um worker de OCR genérico e de alta performance, orientado a eventos via **Apache Kafka** e integrado a sistemas de armazenamento de objetos compatíveis com a API **Amazon S3** (incluindo AWS S3 oficial, EVEO S3-compatible, MinIO, etc.). 

O serviço consome requisições de OCR do Kafka, baixa o documento correspondente do S3, processa-o localmente (aplicando o motor `ocrmypdf` para gerar PDFs pesquisáveis ou extrair textos) e faz o upload do arquivo resultante de volta para o S3, emitindo eventos de sucesso ou falha no Kafka.

---

## 2. Modelo de Implantação
O worker é arquitetado de modo a manter uma **imagem Docker única** (`docker.io/eurival/gedtotal-ocr-service`), que é reutilizada e implantada em múltiplos fluxos de forma isolada e especializada.

Para cada integração/fluxo, a topologia de implantação consiste em:
* **1 Imagem Docker** comum e independente.
* **1 Deployment** dedicado (gerenciando réplicas e recursos).
* **1 ConfigMap** com as configurações específicas da integração (Kafka, tópicos, bucket, prefixo).
* **1 Secret** contendo as credenciais de acesso exclusivas do storage e outros segredos.
* **1 Consumer Group** próprio no Kafka para garantir leitura independente e sem concorrência entre fluxos.

---

## 3. Matriz dos Deployments

Abaixo está a configuração operacional de cada um dos deployments ativos que utilizam o worker:

| Característica | `gedtotal-ocr-service` (Legado) | `licitai-ocr-service` (Licitações) | `licitai-documento-ocr-service` (Empresas) |
| :--- | :--- | :--- | :--- |
| **Tópico de Entrada** | `arquivos-processar-gedtotal-ocr` | `licitai.ocr.requests` | `licitai.documento.ocr.solicitado` |
| **Tópico de Saída** | `extrair-texto-pdf` | `licitai.ocr.results` | `licitai.documento.ocr.processado` |
| **Tópico de Falha** | `arquivos-processar-gedtotal-ocr-falha` | `licitai.ocr.failures` | `licitai.documento.ocr.falhou` |
| **Consumer Group** | `gedtotal-ocr-service` | `licitai-ocr-service` | `licitai-documento-ocr-service` |
| **Endpoint Storage** | *(AWS S3 Padrão)* | `https://object.sp2.eveo.com.br` | `https://object.sp2.eveo.com.br` |
| **S3 Bucket** | `gedtotal` | `licitaglobal` | `licitaglobal` |
| **Prefixo Permitido** | `""` (Livre) | `licitai/ocr/licitacoes/` | `documentos/` |
| **Modo de Output** | `OVERWRITE` (Sobrescrever) | `NEW_OBJECT` | `NEW_OBJECT` |

---

## 4. Variáveis de Ambiente

O comportamento do worker é configurado através das seguintes variáveis de ambiente:

| Variável | Obrigatória | Valor Padrão | Descrição | Exemplo |
| :--- | :---: | :--- | :--- | :--- |
| `KAFKA_BOOTSTRAP_SERVERS` | **Sim** | `15.229.173.87:19092` | Endereço dos brokers do Kafka | `localhost:9092` |
| `KAFKA_INPUT_TOPIC` | **Sim** | *Nenhum* | Tópico de entrada para solicitações de OCR | `licitai.ocr.requests` |
| `KAFKA_OUTPUT_TOPIC` | **Sim** | *Nenhum* | Tópico para emitir mensagens de sucesso | `licitai.ocr.results` |
| `KAFKA_FAILURE_TOPIC` | **Sim** | *Nenhum* | Tópico para emitir mensagens de falha | `licitai.ocr.failures` |
| `KAFKA_GROUP_ID` | **Sim** | *Nenhum* | ID do consumer group no Kafka | `licitai-ocr-service` |
| `KAFKA_AUTO_OFFSET_RESET` | Não | `earliest` | Política do Kafka para novos consumers | `latest` |
| `STORAGE_PROVIDER` | Não | `s3` | Provedor de storage (`s3` / `local`) | `s3` |
| `S3_ENDPOINT` | Não | `""` | Endpoint HTTP/S do S3 (vazio para AWS oficial) | `https://object.sp2.eveo.com.br` |
| `S3_BUCKET` | **Sim** | *Nenhum* | Nome do Bucket S3 de trabalho | `licitaglobal` |
| `S3_REGION` | Não | `sa-east-1` | Região do bucket (fallback para `AWS_REGION`) | `auto` |
| `S3_PATH_STYLE` | Não | `false` | Se usa addressing no formato path-style (`True`) | `true` |
| `S3_VERIFY_SSL` | Não | `true` | Se deve validar certificados SSL nas conexões S3 | `false` |
| `S3_ALLOWED_PREFIX` | Não | `""` | Restringe a execução do OCR a chaves com este prefixo | `documentos/` |
| `AWS_ACCESS_KEY_ID` | **Sim** | *Nenhum* | ID da chave de acesso do S3 | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | **Sim** | *Nenhum* | Chave de acesso secreta do S3 | `vI55...` |
| `AWS_SESSION_TOKEN` | Não | `""` | Token de sessão temporário (opcional) | `IQoJb3JpZ2luX2Vj...` |
| `OCR_LANGUAGE` | Não | `por` | Idioma a ser utilizado no Tesseract OCR | `por+eng` |
| `OCR_JOBS` | Não | *Auto (número de CPUs)* | Número de subprocessos paralelos do OCR | `4` |
| `OCR_OUTPUT_TYPE` | Não | `pdfa` | Tipo do arquivo de saída (`pdfa`, `pdf`, `txt`) | `pdfa` |
| `OCR_OUTPUT_SUFFIX` | Não | `-ocr` | Sufixo aplicado no arquivo de saída no modo `NEW_OBJECT` | `-ocr` |

---

## 5. Exemplos de Providers S3

### Exemplo 1: AWS S3 Oficial
```properties
STORAGE_PROVIDER=s3
S3_ENDPOINT=""
S3_BUCKET=gedtotal
S3_REGION=sa-east-1
S3_PATH_STYLE=false
```

### Exemplo 2: EVEO S3-Compatible (LicitAI)
```properties
STORAGE_PROVIDER=s3
S3_ENDPOINT=https://object.sp2.eveo.com.br
S3_BUCKET=licitaglobal
S3_REGION=auto
S3_PATH_STYLE=true
```

### Exemplo 3: MinIO Local (Desenvolvimento)
```properties
STORAGE_PROVIDER=s3
S3_ENDPOINT=http://localhost:9000
S3_BUCKET=my-local-bucket
S3_REGION=us-east-1
S3_PATH_STYLE=true
S3_VERIFY_SSL=false
```

---

## 6. Contrato de Comunicação Kafka

O contrato de dados é assíncrono e baseado em payloads JSON.

### A. Solicitação (Request Payload)
Enviado pela API Java para o tópico de entrada:
```json
{
  "id": 9198398,
  "caminhoarquivo": "documentos/1/empresas/1/9198398/original.pdf",
  "traceId": "licitai-ocr-documento-9198398-eb53865f",
  "sourceSystem": "LICITAI",
  "tenant": "1",
  "callbackTopic": "licitai.documento.ocr.processado",
  "failureTopic": "licitai.documento.ocr.falhou",
  "outputMode": "NEW_OBJECT",
  "outputSuffix": "-ocr"
}
```

### B. Resultado de Sucesso (Result Payload)
Publicado pelo worker no tópico indicado por `callbackTopic`:
```json
{
  "id": 9198398,
  "caminhoarquivo": "documentos/1/empresas/1/9198398/original-ocr.pdf",
  "ocrApplied": true,
  "traceId": "licitai-ocr-documento-9198398-eb53865f",
  "hashSha256": "58fc321ba51a7b251aec767c80a8b10676f4dbd9297d312efbfa4c7f09c16540",
  "sourceSystem": "LICITAI",
  "tenant": "1"
}
```

### C. Resultado de Falha (Failure Payload)
Publicado no tópico indicado por `failureTopic`:
```json
{
  "id": 9198398,
  "caminhoarquivo": "documentos/1/empresas/1/9198398/original.pdf",
  "errorCode": "OCR_JOB_ERROR",
  "errorMessage": "Acesso negado: chave S3 fora do prefixo permitido",
  "traceId": "licitai-ocr-documento-9198398-eb53865f",
  "sourceSystem": "LICITAI",
  "tenant": "1"
}
```

---

## 7. Estratégia de Organização no LicitAI

Com o alinhamento das configurações, o bucket canônico e unificado para novos arquivos do LicitAI é o **`licitaglobal`**. A separação lógica é feita estritamente por prefixos, protegendo as informações de cada domínio:

* **Documentos de Empresas:**
  * **Chave S3:** `documentos/{consultorId}/empresas/{empresaId}/{documentoId}/...`
  * **Filtro de Prefixo no Deployment:** `S3_ALLOWED_PREFIX=documentos/`
* **Arquivos e OCR de Licitações:**
  * **Chave S3:** `licitai/ocr/licitacoes/{licitacaoId}/arquivos/{arquivoLicitacaoId}/...`
  * **Filtro de Prefixo no Deployment:** `S3_ALLOWED_PREFIX=licitai/ocr/licitacoes/`

---

## 8. Compatibilidade Legada

* **Arquivos Antigos:** Os registros antigos armazenados no bucket `licitai-ai-processing` permanecerão intocados. Não haverá migração ou movimentação automática desses objetos.
* **Leitura Híbrida no `licitai-ai-agents`:** O módulo de busca ocr_adapter.py do LicitAI foi atualizado para carregar a coluna `s3_bucket` da tabela `ai_ocr_document` ao verificar registros prontos. Se houver um bucket gravado no banco de dados, o download é feito deste bucket específico; caso contrário, é utilizado o padrão configurado globalmente (`licitaglobal`).

---

## 9. Segurança

1. **Separação por Secrets:** Cada um dos deployments (`gedtotal-ocr-service`, `licitai-ocr-service`, `licitai-documento-ocr-service`) possui seu próprio objeto de `Secret` Kubernetes. Isso possibilita a rotação de chaves e o controle fino de credenciais.
2. **Princípio do Menor Privilégio:** As chaves de acesso AWS/EVEO associadas ao `licitai-documento-ocr-service-secrets` podem ter suas políticas de IAM/S3 restritas exclusivamente ao prefixo `documentos/*`, enquanto o `licitai-ocr-service-secrets` pode ser restrito a `licitai/ocr/licitacoes/*`.
3. **Sem Credenciais em Trânsito:** Não são trafegadas credenciais de acesso nos payloads Kafka nem registradas em arquivos de log.

---

## 10. Operação e Diagnóstico

Para monitorar e diagnosticar o status das filas utilizando a CLI do Redpanda (`rpk`), utilize os comandos:

```bash
# Listar todos os grupos de consumo e validar conexao
rpk group list -b 15.229.173.87:19092

# Verificar offsets e lag do grupo do novo servico de documentos
rpk group describe licitai-documento-ocr-service \
  -b 15.229.173.87:19092

# Consumir uma mensagem pontual do topico de solicitacoes para fins de teste
rpk topic consume licitai.documento.ocr.solicitado \
  -b 15.229.173.87:19092 \
  -n 1
```

> [!WARNING]
> Consumir mensagens de um tópico especificando um grupo de consumo ativo com o `rpk` pode deslocar o offset de leitura e causar pulo de processamento de mensagens no worker oficial. Sempre execute diagnósticos de leitura sem especificar grupos persistentes em produção.

---

## 11. Diretrizes Técnicas de Storage, Credenciais e Limitações

### A. Políticas de Credenciais S3 e Autenticação
* **Credential Provider Chain**: É suportada nativamente em todos os conectores. Se chaves de acesso estáticas forem omitidas nas variáveis de ambiente, o `boto3` recorrerá à cadeia padrão para obter credenciais (ex: EKS Web Identity, IAM Roles, variáveis nativas).
* **EVEO com Secret Mandatório**: O provedor EVEO, por ser externo e S3 compatível, não possui equivalentes a IAM Roles no cluster Kubernetes de produção atual. Logo, o uso de `Secret` com chaves estáticas (`AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY`) continua operacionalmente necessário para conexões na EVEO.
* **Exigência de Chaves em Par**: Se alguma credencial estática for configurada, o par (Access + Secret) deve ser integralmente preenchido. A definição de apenas um deles invalida o startup ou o processamento.
* **Session Token Temporário**: O `AWS_SESSION_TOKEN` (ou equivalente de OCR) não pode ser configurado de forma isolada; ele depende do par principal de chaves para ser considerado válido.
* **Região `auto` Literal**: A região `"auto"` literal configurada é integralmente preservada e repassada ao boto3 para calcular corretamente o escopo de assinatura SigV4 de endpoints como o da EVEO.

### B. Independência de Perfis por Fluxo
* **Sem Unificação de Perfis**: Cada módulo preserva suas variáveis de configuração operacionais e isolamento de storage.
* **Bucket Dinâmico vs Provider Dinâmico**: O uso de buckets dinâmicos nos registros de banco de dados não confere suporte automático a múltiplos endpoints ou credenciais em tempo de execução. O worker está configurado para operar em um provedor por vez.
* **Compatibilidade Pendente com `licitai-ai-processing`**: Como os workers estão sob o profile EVEO, eles não conseguem acessar o bucket AWS legado. A tentativa de acessar registros com este bucket gerará uma exceção explícita de erro controlado `LEGACY_STORAGE_PROFILE_UNAVAILABLE`.

### C. Contratos Kafka e Readiness
* **Semântica do Evento `ocr.processado`**: O fluxo de validação de documentos empresariais (`DocumentoEmpresa`) exige estritamente a presença da propriedade `caminhoarquivo` contendo a chave do objeto resultante do processamento de OCR. Caso esteja ausente ou vazia, o consumer rejeitará o processamento gerando o erro de falha controlado `OCR_PROCESSED_EVENT_WITHOUT_OUTPUT_KEY`.
* **readiness do Worker**: O status `UP` do endpoint de monitoramento (readiness) valida a conectividade síncrona com o broker Apache Kafka, mas **não valida** a integridade ou o acesso efetivo do worker ao bucket S3 configurado. Credenciais expiradas ou buckets incorretos devem ser monitorados por meio de alertas específicos de falha de processamento.
