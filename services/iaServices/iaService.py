import os
import chromadb
import torch
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EMBEDDINGS_DIR = os.getenv("EMBEDDINGS_DIR", os.path.join(BASE_DIR, "models/multilingual-e5-small"))
MODEL_DIR = os.getenv("MODEL_DIR", os.path.join(BASE_DIR, "models/llama-3.2-3b-instruct"))
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", os.path.join(BASE_DIR, "database/vectorDatabase/chroma_db"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "database")

MAX_CONTEXT_TOKENS = 1200
MAX_INPUT_TOKENS = 668
MAX_NEW_TOKENS = 96

QUERY = 3


def ensure_dir(path: str, label: str) -> None:
    if not os.path.isdir(path):
        raise FileNotFoundError(f"O caminho de {label} nao foi encontrado: {path}")


def load_resources():
    ensure_dir(MODEL_DIR, "modelo principal")
    ensure_dir(EMBEDDINGS_DIR, "modelo de embeddings")

    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDINGS_DIR
    )
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    collection = client.get_or_create_collection(
        COLLECTION_NAME,
        embedding_function=embedding_function,
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_DIR,
        local_files_only=True,
    )

    if torch.cuda.is_available():
        model = model.to("cuda")

    return tokenizer, model, collection


def truncate_context(context, tokenizer, max_tokens=MAX_CONTEXT_TOKENS):
    context_tokens = tokenizer(
        context,
        return_tensors="pt",
        truncation=True,
        max_length=max_tokens,
        add_special_tokens=False,
    )["input_ids"][0]
    return tokenizer.decode(context_tokens, skip_special_tokens=True)


def build_prompt(context, user_input):
    return [
        {
            "role": "system",
            "content": (
                "Voce responde apenas com base no contexto fornecido. "
                "Se nao houver informacao suficiente no contexto, responda exatamente: Não sei."
                "Caso a pergunta do usuario não seja sobre tatuagem, responda: Não sei."
                "Se a pergunta for sobre dificuldade, use exatamente um destes niveis: "
                "Baixa, Media, Alta, Muito Alta ou Insuficiente. "
                "as respostas devem seguir o padrao: Nivel: <nivel> - Justificativa: <justificativa>"
                "Depois do nivel, escreva uma justificativa curta em portugues."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Contexto:\n{context}\n\n"
                f"Pergunta: {user_input}\n"
                "Responda em portugues, de forma objetiva e sem inventar informacoes."
            ),
        },
    ]


def build_response(question, context, tokenizer, model):
    truncated_context = truncate_context(context, tokenizer)
    messages = build_prompt(truncated_context, question)

    prompt_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(
        prompt_text,
        return_tensors="pt",
        truncation=True,
        max_length=MAX_INPUT_TOKENS,
    )
    inputs = {key: value.to(model.device) for key, value in inputs.items()}

    model.eval()
    print("Gerando resposta...")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            use_cache=True,
        )
        prompt_length = inputs["input_ids"].shape[1]

    answer = tokenizer.decode(
        outputs[0][prompt_length:],
        skip_special_tokens=True,
    ).strip()

    return answer or "Nao consegui gerar uma resposta com base no contexto."


def rag_chain(question, tokenizer, model, collection, n_results=QUERY):
    results = collection.query(
        query_texts=[question],
        n_results=n_results,
    )
    context = "\n\n".join(results["documents"][0]) if results["documents"] else ""
    return build_response(question, context, tokenizer, model)


def answer_question(question: str) -> str:
    tokenizer, model, collection = load_resources()
    return rag_chain(question, tokenizer, model, collection)
