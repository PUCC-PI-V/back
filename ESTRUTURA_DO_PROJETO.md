# Estrutura do projeto — pastas e funções (visão básica)

Este ficheiro descreve, de forma simples, **o papel de cada pasta** e **o que as principais funções fazem**. O ponto de entrada da API é o `index.py` na raiz (não é uma pasta, mas monta o FastAPI, CORS, rotas e o arranque com Uvicorn).

---

## `controllers/`

**Função da pasta:** camada entre as **rotas HTTP** e os **serviços**. Recebe o pedido, valida dados mínimos e chama a lógica pesada nos `services/`.

### `controllers/iaControllers/iaController.py`

| Função | O que faz (resumido) |
|--------|----------------------|
| `prompt_index(request)` | Lê o JSON do corpo, extrai a pergunta, carrega modelos + Chroma via `iaService`, devolve a resposta do RAG ou erros HTTP. |

**Pedido HTTP:** `POST /ia/prompt` (definido na rota; ver secção `routes/`).

**Entrada (corpo JSON)** — aceita **uma** destas chaves para a pergunta:

```json
{
  "prompt": "Qual a dificuldade de se realizar um leão geométrico e realista?"
}
```

ou, de forma equivalente:

```json
{
  "input": "Qual a dificuldade de se realizar um leão geométrico e realista?"
}
```

**Saída (sucesso, HTTP 200):**

```json
{
  "answer": "texto gerado pelo modelo com base no contexto recuperado da base vetorial"
}
```

**Outras saídas possíveis:**

- **400** — pergunta vazia (nem `input` nem `prompt` com texto útil).
- **429** — demasiados pedidos no mesmo minuto (rate limit na rota).
- **500** — falha ao carregar recursos (pastas/modelos em falta) ou erro inesperado na geração; o `detail` traz uma mensagem em texto.

---

## `routes/`

**Função da pasta:** define **URLs**, métodos HTTP e regras por cima do controller (ex.: limite de taxa). O `index.py` inclui estes routers com um prefixo.

### `routes/iaRoutes/iaRoute.py`

| Função | O que faz (resumido) |
|--------|----------------------|
| `prompt(request)` | Rota `POST /prompt` no router; aplica limite **5/minuto** por IP e delega em `iaController.prompt_index`. |

Na aplicação final, o URL completo fica **`POST /ia/prompt`** porque o `index.py` faz `include_router(..., prefix="/ia")`.

---

## `services/`

**Função da pasta:** **lógica de negócio** e integrações (IA, e-mail). Não conhece detalhes de “URL”; recebe dados e devolve resultados ou deixa exceções para o controller tratar.

### `services/iaServices/iaService.py`

| Função | O que faz (resumido) |
|--------|----------------------|
| `ensure_dir(path, label)` | Garante que uma pasta existe; senão, lança erro claro. |
| `load_resources()` | Carrega tokenizer + modelo LLM (ficheiros locais), abre o Chroma na pasta configurada e devolve `(tokenizer, model, collection)`. |
| `truncate_context(...)` | Corta o texto de contexto para não exceder um tamanho em tokens. |
| `build_prompt(context, user_input)` | Monta as mensagens `system` + `user` para o modelo (instruções + contexto + pergunta). |
| `build_response(...)` | Aplica o template de chat, corre `model.generate` e devolve a **string** da resposta. |
| `rag_chain(question, tokenizer, model, collection)` | Faz **query** no Chroma com a pergunta, junta os documentos recuperados como contexto e chama `build_response`. |
| `answer_question(question)` | Atalho: `load_resources()` + `rag_chain` numa só chamada (útil para scripts). |

**Entrada/saída (nível serviço):** recebe **strings** e objetos já carregados; a **saída** da cadeia RAG é sempre uma **string** (`answer` no controller é esse texto).

### `services/emailServices/emailService.py`

| Função | O que faz (resumido) |
|--------|----------------------|
| `send_email(tattoo_description, form_link, client_name, subject)` | Usa OAuth Gmail (`credentials.json` / `token.json`), monta e-mail em texto + HTML (com imagem opcional em `assets/`) e envia para `EMAIL_TO` a partir de `EMAIL_FROM` (definidos no `.env`). |

**Entrada:** parâmetros Python (strings), não é um endpoint REST neste ficheiro.

**Saída:** envia o e-mail na API do Gmail; não devolve JSON de API ao utilizador a menos que outro código envolva esta função numa rota.

---

## `utils/`

**Função da pasta:** **utilitários** de instalação e arranque (baixar modelos, decidir se precisa de reindexar).

### `utils/installModels/autoInstallModels.py`

| Função | O que faz (resumido) |
|--------|----------------------|
| `autoInstallModels()` | Se faltar pasta de embeddings ou LLM, chama `download_model()`. Se não existir pasta do Chroma, chama `download_datas()`. Usado ao correr `python index.py`. |

**Entrada/saída:** sem argumentos; usa variáveis de ambiente e imprime mensagens no consola.

### `utils/installModels/installModels.py`

| Função | O que faz (resumido) |
|--------|----------------------|
| `download_model()` | Com `HF_TOKEN`, descarrega o Llama 3.2 3B e grava embeddings `multilingual-e5-small` nas pastas `./models/...` relativas ao diretório de trabalho. |

**Entrada:** `HF_TOKEN` no `.env`. **Saída:** pastas criadas em disco ou mensagem de erro / saída antecipada.

---

## `database/`

**Função da pasta:** dados **persistidos** ou usados para **vetorização** (texto-fonte, ChromaDB).

### `database/vectorDatabase/`

| Ficheiro / pasta | Função (resumido) |
|------------------|-------------------|
| `source_data.txt` | Texto com “perguntas” (linhas a terminar em `?`) e blocos de resposta — fonte do contexto do RAG. |
| `chroma_db/` (gerada) | Base vetorial Chroma em disco (criada pelo script de dados). |
| `downloadDatas.py` | Lê `SOURCE_DATA_PATH`, parte em entradas (`parse_faq_entries`), cria/atualiza a coleção Chroma com embeddings locais. |

Funções principais em `downloadDatas.py`:

| Função | O que faz (resumido) |
|--------|----------------------|
| `ensure_local_path(path, label)` | Confirma que o caminho dos embeddings existe. |
| `parse_faq_entries(text)` | Converte o `.txt` numa lista de `{question, answer, document}`. |
| `download_datas()` | Apaga/recria coleção, insere documentos no Chroma. |

**Entrada:** ficheiro de texto + pasta de embeddings + nome da coleção (via `.env`). **Saída:** mensagem no consola com o número de entradas indexadas.

---

## `models/`

**Função da pasta:** armazenar **modelos em disco** depois do download (por exemplo `llama-3.2-3b-instruct` e `multilingual-e5-small`). Não costuma ir para o Git em repositórios reais (ficheiros muito grandes). Os caminhos exatos vêm do `.env` (`MODEL_DIR`, `EMBEDDINGS_DIR`) ou dos defaults do código / scripts.

---

## `Projeto Integrador V - bruno api test/`

**Função da pasta:** coleção **Bruno** (cliente de API) com pedidos HTTP em `.yml` para testar manualmente a API em execução (ex.: `GET /status`, `POST /ia/prompt`). Não executa código Python do backend; só guarda definições de testes.

---

## Resumo visual do fluxo do `/ia/prompt`

```text
Cliente HTTP
    → routes/iaRoutes (limite + POST /prompt)
        → controllers/iaControllers (lê JSON, valida)
            → services/iaServices (RAG + geração)
                → database/vectorDatabase/chroma_db (contexto)
                → models/ (LLM + embeddings)
    ← JSON { "answer": "..." }
```

Para mais detalhes de instalação e execução, vê o `README.md`.
