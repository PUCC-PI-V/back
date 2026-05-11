# Backend ViboraInk — API FastAPI (IA RAG + e-mail)

Documentação focada em **como instalar, configurar e executar** o projeto. A API expõe rotas de status, prompt com RAG (ChromaDB + modelo local) e, em código separado, envio de e-mail via Gmail.

---

## Pré-requisitos

- **Python 3.11+** (recomendado; o projeto usa PyTorch, Transformers, ChromaDB).
- **Espaço em disco** para modelos (ordem de vários GB: LLM + embeddings).
- Conta **Hugging Face** com token para baixar o modelo **Llama 3.2 3B Instruct** (gated).
- **GPU NVIDIA** opcional; sem GPU o carregamento e a inferência ficam mais lentos.

---

## Instalação

### 1. Entrar na pasta do projeto

```powershell
cd c:\back
```

(Ajuste o caminho se o repositório estiver em outro lugar.)

### 2. Criar o ambiente virtual (venv)

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (cmd):**

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Atualizar o pip (recomendado)

```powershell
python -m pip install --upgrade pip
```

### 4. Instalar dependências a partir do `requirements.txt`

```powershell
pip install -r requirements.txt
```

### 5. Se a instalação falhar

Erros comuns: conflito de versão, falta de compilador no Windows para algum pacote, timeout de rede, ou índice PyPI lento.

Tente, nesta ordem:

1. Instalar de novo com log verboso: `pip install -r requirements.txt -v`
2. Instalar **PyTorch** conforme a [página oficial](https://pytorch.org/) do seu SO/CUDA, depois rodar `pip install -r requirements.txt` de novo.
3. Instalar pacotes manualmente (mesmas versões do `requirements.txt` quando possível). Lista completa dos pacotes pinados no repositório:

`annotated-doc`, `annotated-types`, `anyio`, `attrs`, `bcrypt`, `build`, `certifi`, `cffi`, `charset-normalizer`, `chromadb`, `click`, `colorama`, `cryptography`, `dotenv`, `durationpy`, `fastapi`, `filelock`, `flatbuffers`, `fsspec`, `google-api-core`, `google-api-python-client`, `google-auth`, `google-auth-httplib2`, `google-auth-oauthlib`, `googleapis-common-protos`, `grpcio`, `h11`, `hf-xet`, `httpcore`, `httplib2`, `httptools`, `httpx`, `huggingface_hub`, `idna`, `importlib_metadata`, `importlib_resources`, `Jinja2`, `joblib`, `jsonschema`, `jsonschema-specifications`, `kubernetes`, `markdown-it-py`, `MarkupSafe`, `mdurl`, `mmh3`, `mpmath`, `networkx`, `numpy`, `oauthlib`, `onnxruntime`, `opentelemetry-api`, `opentelemetry-exporter-otlp-proto-common`, `opentelemetry-exporter-otlp-proto-grpc`, `opentelemetry-proto`, `opentelemetry-sdk`, `opentelemetry-semantic-conventions`, `orjson`, `overrides`, `packaging`, `proto-plus`, `protobuf`, `pyasn1`, `pyasn1_modules`, `pybase64`, `pycparser`, `pydantic`, `pydantic-settings`, `pydantic_core`, `Pygments`, `pyparsing`, `PyPika`, `pyproject_hooks`, `python-dateutil`, `python-dotenv`, `PyYAML`, `referencing`, `regex`, `requests`, `requests-oauthlib`, `rich`, `rpds-py`, `safetensors`, `scikit-learn`, `scipy`, `sentence-transformers`, `setuptools`, `shellingham`, `six`, `starlette`, `sympy`, `tenacity`, `threadpoolctl`, `tokenizers`, `torch`, `tqdm`, `transformers`, `typer`, `typing-inspection`, `typing_extensions`, `uritemplate`, `urllib3`, `uvicorn`, `watchfiles`, `websocket-client`, `websockets`, `zipp`, **`slowapi`**.

Instalação mínima explícita do que o **código importa diretamente** (não substitui o `requirements.txt` inteiro — o Chroma e o Google trazem muitas dependências transitivas):

```text
fastapi uvicorn python-dotenv slowapi
torch transformers sentence-transformers huggingface_hub chromadb
google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Se após `pip install -r requirements.txt` ainda faltar algo, use: `pip install nome-do-pacote` até `python -c "import index"` rodar sem erro.

---

## Variáveis de ambiente: `.env.exemple` → `.env`

No repositório existe o arquivo **`.env.exemple`** (nome com “exemple” de propósito no projeto). Ele é um **modelo**: você deve **copiar** para **`.env`** na raiz do projeto e **preencher** os valores. O aplicativo **não** lê `.env.exemple` automaticamente; quem carrega é o **`python-dotenv`** a partir de **`.env`** quando o código chama `load_dotenv()`.

**Como fazer:**

1. Copie: `copy .env.exemple .env` (Windows) ou `cp .env.exemple .env` (Linux/macOS).
2. Abra `.env` e ajuste cada variável.

**Significado das variáveis no modelo:**

| Variável | Função |
|----------|--------|
| `PORT` | Porta em que o Uvicorn sobe ao rodar `python index.py` (padrão no código também aceita ausência: 8000). Prefira formato `PORT=8080` **sem espaços** ao redor do `=`. |
| `HF_TOKEN` | Token da Hugging Face. **Obrigatório** para o script baixar o modelo Llama 3.2 3B (repositório com acesso restrito). Crie em: *Settings → Access Tokens* no site da HF. |
| `EMBEDDINGS_DIR` | Pasta local do modelo de **embeddings** (`multilingual-e5-small`). |
| `MODEL_DIR` | Pasta local do **LLM** (`llama-3.2-3b-instruct`). |
| `COLLECTION_NAME` | Nome da **coleção ChromaDB** usada no RAG. O serviço de IA usa padrão `database` se não houver `.env`; alinhe este valor com o que foi usado ao popular o banco (veja `downloadDatas.py`). |
| `SOURCE_DATA_PATH` | Arquivo de texto com o **contexto** indexado no Chroma (padrão: `database/vectorDatabase/source_data.txt`). |
| `CHROMA_DB_DIR` | Pasta de persistência do Chroma (padrão: `database/vectorDatabase/chroma_db`). |
| `EMAIL_TO` / `EMAIL_FROM` | Destinatário e remetente para o fluxo de e-mail Gmail (preencha se for usar `emailService`). |

**Dica:** execute sempre `python index.py` **a partir da raiz do projeto** (`c:\back`), para que caminhos relativos como `./models/...` e `./database/...` coincidam com o `.env`.

---

## Dados de contexto para a IA: `database/vectorDatabase/source_data.txt`

O RAG não “inventa” o catálogo de orçamentos: ele consulta trechos guardados no **ChromaDB**, que são gerados a partir deste arquivo.

- **Formato esperado:** blocos estilo FAQ: uma **pergunta** em linha terminada com **`?`**, seguida das linhas de “resposta” (descrição, dificuldade, valor, justificativa, etc.) até a próxima linha que termina com `?`.
- O script `database/vectorDatabase/downloadDatas.py` lê `SOURCE_DATA_PATH` (por padrão esse `source_data.txt`), **parte** o texto em entradas e grava embeddings + metadados na coleção Chroma.
- **Alterar o contexto:** edite `source_data.txt` (ou outro arquivo apontado por `SOURCE_DATA_PATH`) e **reconstrua** o índice. Se a pasta `chroma_db` já existir, `autoInstallModels()` **não** chama de novo o `download_datas`; apague a pasta `chroma_db` ou rode manualmente o script de download para reindexar.

Exemplo de estrutura (resumido): pergunta com `?` na primeira linha do bloco; linhas seguintes são o conteúdo associado até a próxima pergunta.

---

## Como executar: `index.py`

Na raiz, com o venv ativo:

```powershell
python index.py
```

### O que o `index.py` faz

1. Cria a aplicação **FastAPI** (`app`).
2. Associa o **rate limiter** do `slowapi` ao `app` (`app.state.limiter`) e registra o handler de **429** para `RateLimitExceeded`.
3. Chama **`load_dotenv()`** para carregar variáveis de **`.env`**.
4. Lê **`PORT`** do ambiente (padrão **8000** se não existir).
5. Adiciona **CORS** (`localhost` e `localhost:8080`).
6. Registra **`GET /status`** e inclui o router **`/ia`** (`POST /ia/prompt`, com limite `5/minute` por IP).
7. **Somente quando você executa o arquivo como programa principal** (`if __name__ == "__main__"`):
   - Chama **`autoInstallModels()`** (em `utils/installModels/autoInstallModels.py`):
     - Se faltar pasta de embeddings ou de LLM (conforme variáveis de ambiente / defaults), chama **`download_model()`** — baixa da Hugging Face com **`HF_TOKEN`** e grava nas pastas configuradas.
     - Se não existir o diretório do Chroma (`CHROMA_DB_DIR`), chama **`download_datas()`** — lê o texto de contexto, gera embeddings e popula o Chroma.
   - Em seguida sobe o servidor com **`uvicorn.run(app, host="127.0.0.1", port=PORT)`**.

**Importante:** rodar só `uvicorn index:app` **sem** passar pelo bloco `if __name__ == "__main__"` **não** executa `autoInstallModels()`. Para instalação automática na primeira vez, use **`python index.py`** ou chame você mesmo os scripts de modelo/dados antes.

### Alternativa: só o ASGI, sem auto-instalação

```powershell
uvicorn index:app --host 127.0.0.1 --port 8000
```

Útil depois que modelos e Chroma já estão no disco.

---

## Endpoints úteis

| Método | Caminho | Descrição |
|--------|---------|-----------|
| `GET` | `/status` | Verifica se a API está no ar. |
| `POST` | `/ia/prompt` | Corpo JSON: `{"input": "..."}` ou `{"prompt": "..."}`. Resposta: `{"answer": "..."}`. Limite: **5 requisições/minuto** por IP (slowapi). |

Exemplo (PowerShell):

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/ia/prompt" `
  -ContentType "application/json" -Body '{"input":"Qual o valor aproximado de um leão geométrico?"}'
```

---

## Testes de API com Bruno (Projeto Integrador V)

**Bruno** é um cliente de API open-source (alternativa leve a Postman/Insomnia): as coleções ficam em **ficheiros YAML** no repositório, versionáveis e fáceis de partilhar. Site oficial: [usebruno.com](https://www.usebruno.com/).

Neste projeto, a coleção preparada para testar o backend está na pasta (na raiz do repositório):

`Projeto Integrador V - bruno api test/`

### O que há dentro dessa pasta

- **`opencollection.yml`** — metadados da coleção **“Projeto Integrador V”** (nome e opções Bruno).
- **`statusCheck.yml`** — pedido **HTTP GET** a `http://127.0.0.1:8080/status` (verificação de que a API está no ar).
- **`sendMassage.yml`** — pedido **HTTP POST** a `http://127.0.0.1:8080/ia/prompt` com corpo JSON de exemplo (`prompt`: `"hello world!"`).
- **`PI-V/`** — subpasta com pedidos adicionais da mesma coleção (ex.: `opencollection.yml`, outros `.yml`), útil se organizarem variantes do PI no Bruno.

### Como rodar os testes

1. **Instalar o Bruno** (aplicação desktop): descarregue em [usebruno.com/downloads](https://www.usebruno.com/downloads) e instale.
2. **Subir o backend** (`python index.py` ou `uvicorn`) na mesma **porta** que os ficheiros usam (**8080** nos YAML atuais). Se o teu `.env` tiver `PORT=8000`, ou alteras o `.env` para `8080`, ou editas nos `.yml` as URLs para `http://127.0.0.1:8000/...`.
3. No Bruno: **Open Collection** (ou equivalente) e escolhe a pasta **`Projeto Integrador V - bruno api test`** — o Bruno carrega os `.yml` como pedidos da coleção.
4. Abre cada pedido (**statusCheck**, **sendMassage**, etc.) e clica em **Send** para executar contra a API em execução.

**Nota:** o endpoint `/ia/prompt` tem **rate limit (5/minuto)** por IP; vários *Sends* seguidos no Bruno podem devolver **429** — espaça os testes ou ajusta o limite em desenvolvimento.

---

## Erros que podem aparecer

| Sintoma | Causa provável | O que fazer |
|---------|----------------|-------------|
| `HF_TOKEN is not set` / download não inicia | `.env` ausente ou sem token | Copie `.env.exemple` → `.env` e defina `HF_TOKEN`. |
| Erro 401/403 ao baixar Llama | Token inválido ou sem aceite do licenciamento do modelo na Hugging Face | Gere token com permissão de leitura e aceite os termos do modelo na página do repositório. |
| `FileNotFoundError` para modelo ou Chroma | Pastas erradas ou ainda não baixadas | Confira `MODEL_DIR`, `EMBEDDINGS_DIR`, `CHROMA_DB_DIR`. Rode `python index.py` uma vez na raiz ou `installModels` / `downloadDatas` manualmente. |
| `COLLECTION_NAME` / coleção vazia ou não encontrada | Nome da coleção diferente entre indexação e `iaService` | Use o mesmo `COLLECTION_NAME` no `.env` ao popular e ao servir (ex.: `database`). |
| Resposta **429** em `/ia/prompt` | Rate limit | Espere o minuto ou reduza testes automatizados; limite configurado na rota. |
| Erro ao importar `slowapi` | Pacote não instalado | `pip install slowapi` (também consta no `requirements.txt` atual). |
| `ModuleNotFoundError: ...` | Dependência faltando | `pip install -r requirements.txt` ou instale o pacote indicado na mensagem. |
| Erro CUDA / memória | GPU sem VRAM suficiente | Feche outros processos ou rode em CPU (mais lento). |
| E-mail Gmail falhando | OAuth / credenciais | Na raiz, `credentials.json` do Google Cloud; primeiro fluxo gera `token.json`. Preencha `EMAIL_FROM` / `EMAIL_TO` no `.env`. Não commite segredos. |

---

## Scripts manuais (se não quiser depender só do `index.py`)

- **Só modelos:** `python utils/installModels/installModels.py` (ou o módulo equivalente no seu layout) — exige `HF_TOKEN`.
- **Só vetores:** `python database/vectorDatabase/downloadDatas.py` — exige embeddings já instalados e `source_data.txt` (ou caminho em `SOURCE_DATA_PATH`) acessível.

---

## E-mail (Gmail API)

Para usar `services/emailServices/emailService.py`: projeto OAuth no Google Cloud, `credentials.json` na raiz, escopos de envio, e variáveis `EMAIL_FROM` / `EMAIL_TO` no `.env`. O primeiro uso costuma abrir o navegador para autorizar e gravar `token.json`.

---

## Segurança e repositório

- Não versionar **`.env`**, **`credentials.json`**, **`token.json`** nem pastas grandes de modelos/Chroma se a política do time for ignorá-las no Git (ajuste `.gitignore` conforme necessidade).
