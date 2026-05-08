# API de IA + Aviso de Orcamento por E-mail

Backend em **Python + FastAPI** com dois blocos principais:
- **IA (RAG)** para responder perguntas com contexto do ChromaDB.
- **E-mail** para enviar aviso de novo orcamento no layout da ViboraInk.

---

## Endpoints

### `GET /status`
Retorna que a API esta no ar.

### `POST /ia/prompt`
Recebe a pergunta do usuario e retorna resposta do pipeline RAG.

Exemplo de body:
```json
{
  "input": "Qual e a politica de reembolso?"
}
```

Tambem aceita:
```json
{
  "prompt": "Qual e a politica de reembolso?"
}
```

Resposta:
```json
{
  "answer": "..."
}
```

---

## Arquitetura atual (coerente com o codigo)

### `controllers/iaControllers/iaController.py`
O controller do endpoint `/ia/prompt`:
1. Le o JSON da requisicao.
2. Extrai a pergunta de `input` ou `prompt`.
3. Chama `iaService.load_resources()`.
4. Valida pergunta vazia (retorna 400).
5. Chama `iaService.rag_chain(...)`.
6. Retorna `{"answer": answer}`.

Erros inesperados retornam `HTTPException 500`.

### `services/iaServices/iaService.py`
Service com toda logica de IA:
- `load_resources()`: abre modelos locais + ChromaDB.
- `truncate_context(...)`: limita tamanho do contexto.
- `build_prompt(...)`: cria mensagens `system`/`user`.
- `build_response(...)`: aplica chat template e gera resposta.
- `rag_chain(...)`: consulta ChromaDB e chama geracao.

Esse service usa:
- `MODEL_DIR` para o LLM local.
- `EMBEDDINGS_DIR` para embeddings locais.
- `CHROMA_DB_DIR` para persistencia do banco vetorial.
- `COLLECTION_NAME` para selecionar colecao correta.

### `services/emailServices/emailService.py`
Service de envio de e-mail via Gmail API.

Funcao principal:
```python
send_email(
    tattoo_description: str = "",
    form_link: str = "",
    client_name: str = "",
    subject: str = "Novo aviso de orcamento - ViboraInk",
)
```

O que ela faz:
- autentica no Gmail com OAuth (`credentials.json` + `token.json`);
- monta e-mail em texto simples + HTML estilizado;
- inclui imagem inline (`services/emailServices/assets/emailImage.jpg`);
- envia para `EMAIL_TO`, com remetente `EMAIL_FROM`.

---

## Como configurar o projeto

### 1) Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2) Criar `.env` na raiz do projeto
Exemplo:
```env
PORT=8000
HF_TOKEN=SEU_TOKEN_HUGGINGFACE

EMAIL_TO=destinatario@exemplo.com
EMAIL_FROM=seu_email_gmail@exemplo.com

# Opcional (se quiser customizar caminhos)
# EMBEDDINGS_DIR=c:\back\models\multilingual-e5-small
# MODEL_DIR=c:\back\models\llama-3.2-3b-instruct
# CHROMA_DB_DIR=c:\back\database\vectorDatabase\chroma_db
# COLLECTION_NAME=database
```

### 3) Baixar modelos locais (IA)
```bash
python installModels.py
```

### 4) Popular base vetorial (RAG)
```bash
python database/vectorDatabase/downloadDatas.py
```

### 5) Rodar a API
```bash
python index.py
```
ou
```bash
uvicorn index:app --reload --port 8000
```

---

## Gmail API: `credentials.json` e `token.json` (importante)

Para o `emailService.py` funcionar, o fluxo OAuth do Google precisa estar correto.

### O que e `credentials.json`
- Arquivo baixado do **Google Cloud Console**.
- Contem `client_id` e `client_secret` do app OAuth.
- Deve ficar na raiz do projeto (mesmo nivel do `index.py`, para bater com `from_client_secrets_file('credentials.json', ...)`).

### O que e `token.json`
- Arquivo gerado automaticamente no **primeiro login**.
- Guarda `access_token` e `refresh_token` do usuario autorizado.
- Nas proximas execucoes, o codigo reutiliza esse arquivo e tenta renovar token sem abrir navegador.

### Fluxo de primeira execucao
1. Voce chama `send_email(...)`.
2. Se `token.json` nao existe, abre navegador (`flow.run_local_server(...)`).
3. Voce faz login na conta Google e concede permissao `gmail.send`.
4. O sistema grava `token.json`.
5. A partir dai, o envio funciona sem login manual (enquanto o refresh token for valido).

### Quando apagar o `token.json`
Apague e gere de novo quando:
- mudar o escopo (`SCOPES`);
- trocar `credentials.json`;
- mudar de conta Google;
- token ficar invalido/revogado.

### Checklist rapido para nao falhar envio
- `credentials.json` valido na raiz.
- `EMAIL_FROM` e `EMAIL_TO` definidos no `.env`.
- primeira autorizacao concluida no navegador.
- permissao Gmail API habilitada no projeto do Google Cloud.

---

## Exemplo de chamada do endpoint IA (PowerShell)
```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/ia/prompt" -ContentType "application/json" -Body '{
  "input": "Qual e a politica de reembolso?"
}'
```

---

## Observacoes
- O carregamento dos modelos de IA e local (`local_files_only=True`).
- Se nao houver GPU, funciona em CPU (mais lento).
- O `.gitignore` ja ignora `*.json`, entao `credentials.json` e `token.json` nao devem ir para o repositorio.

