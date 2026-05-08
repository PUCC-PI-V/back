# Projeto Integrador V - API de IA (RAG)

Este projeto é uma API em **Python + FastAPI** que implementa um pipeline de **RAG (Retrieval-Augmented Generation)**:
1. Busca contexto em um banco vetorial (**ChromaDB**).
2. Monta um prompt com o contexto recuperado.
3. Gera a resposta com um modelo de linguagem (**Transformers**).

## Rotas (endpoints)

### `GET /status`
Retorna uma mensagem confirmando que o backend está em execução.

### `POST /ia/prompt`
Gera uma resposta a partir de uma pergunta do usuário.

Corpo (JSON):
```json
{
  "input": "sua pergunta aqui"
}
```

Opcionalmente, você também pode enviar:
```json
{
  "prompt": "sua pergunta aqui"
}
```

Resposta (JSON):
```json
{
  "answer": "resposta gerada..."
}
```

## Como funciona o roteador (Router)

O projeto usa o padrão do FastAPI:

### `index.py` (montagem do app)
- Cria a aplicação:
  - `app = FastAPI()`
- Define a rota de saúde:
  - `@app.get("/status")`
- Registra o módulo de rotas da IA:
  - `app.include_router(iaRoute.router, prefix="/ia")`

Isso significa que qualquer rota definida no `iaRoute.router` ganha automaticamente o prefixo **`/ia`**.

### `routes/iaRoutes/iaRoute.py` (rotas do módulo)
- Cria um roteador:
  - `router = APIRouter()`
- Define o endpoint:
  - `@router.post("/prompt")`
- A função do endpoint apenas encaminha a requisição:
  - `return await iaController.prompt_index(request)`

Assim, a rota final vira: **`POST /ia/prompt`**.

## Instalação e execução

### 1) Instale as dependências
Com Python instalado (recomendado 3.10+), instale:
```bash
pip install -r requirements.txt
```

### 2) Configure variáveis de ambiente (`.env`)
O código usa `load_dotenv()`. Crie um arquivo `.env` na raiz `c:\back` com, por exemplo:
```env
PORT=8000
HF_TOKEN=SEU_TOKEN_HUGGINGFACE (apenas se for baixar modelos)

# (opcional) diretos customizados:
# IMPORTANTE: `installModels.py` salva embeddings em `./models/...`
# então defina `EMBEDDINGS_DIR` apontando para essa pasta (para bater com o `iaController.py`).
#
# Também ajuste `COLLECTION_NAME` para ser o MESMO valor entre `iaController.py` e `downloadDatas.py`.
#
# Exemplo (recomendado):
# EMBEDDINGS_DIR=c:\back\models\multilingual-e5-small
# MODEL_DIR=c:\back\models\llama-3.2-3b-instruct
# CHROMA_DB_DIR=c:\back\database\vectorDatabase\chroma_db
# COLLECTION_NAME=database
# SOURCE_DATA_PATH=c:\back\database\vectorDatabase\source_data.txt
```

### 3) Baixe os modelos localmente (necessário)
O controlador carrega modelos com `local_files_only=True`, então os arquivos precisam existir em disco.

Execute:
```bash
python installModels.py
```

Esse script:
- Baixa o LLM `meta-llama/Llama-3.2-3B-Instruct`
- Baixa o modelo de embeddings `intfloat/multilingual-e5-small`
- Salva em:
  - `./models/llama-3.2-3b-instruct`
  - `./models/multilingual-e5-small`

### 4) Monte o banco vetorial (ChromaDB)
Para o RAG funcionar, é preciso criar/popular a coleção no ChromaDB.

Execute:
```bash
python database/vectorDatabase/downloadDatas.py
```

Esse script:
- Lê `SOURCE_DATA_PATH` (default: `database/vectorDatabase/source_data.txt`)
- Divide o texto em entradas considerando perguntas que terminam com `?`
- Cria um `document` por entrada contendo:
  - `passage: <pergunta>\n<resposta>`
- Cria uma coleção no ChromaDB com embeddings do modelo local
- Apaga a coleção anterior com o mesmo nome (via `delete_collection`)

Repare que `downloadDatas.py` precisa usar os mesmos valores de `EMBEDDINGS_DIR` e `COLLECTION_NAME` que o `iaController.py`, senão o endpoint vai consultar uma base diferente.

### 5) Rode a API
Opção A (direto):
```bash
python index.py
```

Opção B (uvicorn):
```bash
uvicorn index:app --reload --port 8000
```

## Fluxo interno (funções principais)

### `controllers/iaControllers/iaController.py`

#### `load_resources()`
Carrega todos os recursos necessários:
- Verifica se as pastas do modelo e embeddings existem (via `ensure_dir`)
- Configura embeddings:
  - `SentenceTransformerEmbeddingFunction(model_name=EMBEDDINGS_DIR)`
- Inicializa/abre o ChromaDB:
  - `chromadb.PersistentClient(path=CHROMA_DB_DIR)`
  - `client.get_or_create_collection(COLLECTION_NAME, embedding_function=...)`
- Carrega tokenizer e modelo LLM localmente:
  - `AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)`
  - `AutoModelForCausalLM.from_pretrained(MODEL_DIR, local_files_only=True)`
- Se houver GPU (`torch.cuda.is_available()`), move o modelo para `cuda`.

#### `truncate_context(context, tokenizer, max_tokens=MAX_CONTEXT_TOKENS)`
Reduce o tamanho do contexto recuperado para caber no limite de tokens do prompt.

#### `build_prompt(context, input)`
Monta a lista de mensagens (formato chat) para o LLM:
- `system`: instruções para responder **apenas** com base no contexto
- `user`: inclui `Contexto` + `Pergunta`

#### `build_response(question, context, tokenizer, model)`
1. Trunca o contexto
2. Constrói o texto final do prompt via `tokenizer.apply_chat_template(...)`
3. Tokeniza e envia para o device do modelo (`model.device`)
4. Gera a resposta com `model.generate(...)` usando:
   - `do_sample=False` (geração determinística)
   - `max_new_tokens=MAX_NEW_TOKENS`
5. Faz decode apenas da parte gerada (remove o prompt do começo).

Se nada for gerado, retorna:
`"Nao consegui gerar uma resposta com base no contexto."`

#### `rag_chain(question, tokenizer, model, collection, n_results=QUERY)`
Implementa o “R”:
- Consulta o ChromaDB com:
  - `collection.query(query_texts=[question], n_results=n_results)`
- Junta os `documents` retornados como `context`
- Retorna o resultado de `build_response(...)`.

#### `prompt_index(request: Request)` (endpoint lógico)
Função acionada pelo roteador do endpoint `POST /ia/prompt`:
- Lê JSON da requisição e extrai `input` (ou `prompt`)
- Carrega recursos (`load_resources()`)
- Valida se a pergunta não está vazia
- Chama `rag_chain(...)`
- Retorna `{"answer": answer}`
- Em erros, retorna `HTTPException` com status 400/500.

### `installModels.py`
- `download_model()`: baixa e salva modelos via Hugging Face.
- Exige `HF_TOKEN` (se o download for necessário).

### `database/vectorDatabase/downloadDatas.py`
- `parse_faq_entries(text)`: cria entradas a partir do arquivo fonte
- Fluxo principal: cria/popula o ChromaDB usando embeddings locais.

## Exemplo de chamada (PowerShell)

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/ia/prompt" -ContentType "application/json" -Body '{
  "input": "Qual é a política de reembolso?"
}'
```

## Observações importantes
- O modelo LLM e embeddings são carregados **localmente** (`local_files_only=True`): primeiro rode `installModels.py`.
- A API tenta usar GPU quando disponível, mas funciona em CPU (pode ficar mais lento).
- O contexto vem do ChromaDB: se a base vetorial não existir/estiver vazia, a resposta tende a ser “Nao sei” (por causa do `system prompt`).

