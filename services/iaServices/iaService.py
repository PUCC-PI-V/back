import os
import re
import threading
import chromadb
import torch
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EMBEDDINGS_DIR = os.getenv("EMBEDDINGS_DIR", os.path.join(BASE_DIR, "models/multilingual-e5-small"))
MODEL_DIR = os.getenv("MODEL_DIR", os.path.join(BASE_DIR, "models/llama-3.2-1b-instruct"))
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", os.path.join(BASE_DIR, "database/vectorDatabase/chroma_db"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "database")

MAX_CONTEXT_TOKENS = 1200
MAX_INPUT_TOKENS = 668
MAX_NEW_TOKENS = 96
MAX_BUDGET_NEW_TOKENS = 160

QUERY = 3

_chroma_cache = None
_llm_cache = None
_resources_lock = threading.Lock()

DIFFICULTY_LEVELS = ("Baixa", "Media", "Alta", "Muito Alta", "Insuficiente")

SYSTEM_PROMPT_CHAT = (
    "Voce e um assistente de tatuagem.\n"
    "Regras:\n"
    "1. Use apenas o contexto fornecido.\n"
    "2. Se faltar informacao ou a pergunta nao for sobre tatuagem, responda exatamente: Nao sei.\n"
    "3. Responda em portugues, de forma curta e objetiva.\n"
    "4. Nao invente precos, niveis ou detalhes que nao estejam no contexto."
    "5. Deve mandar somente a resposta, então nada de Resposta: ou coisa do tipo"
)

SYSTEM_PROMPT_BUDGET = (
    "Voce estima orcamentos de tatuagem.\n"
    "Regras:\n"
    "1. Use apenas o contexto fornecido.\n"
    "2. Se faltar informacao, responda exatamente: Nao sei.\n"
    "3. O contexto usa este formato coletado:\n"
    "DIFICULDADE TECNICA: <texto>\n"
    "VALOR APROXIMADO: R$<valor>\n"
    "JUSTIFICATIVA DA DIFICULDADE: <texto>\n"
    "4. Leia o contexto nesse formato, mas responda convertendo para o formato abaixo.\n"
    "5. Converta a dificuldade assim: Facil->Baixa, Medio->Media, Dificil->Alta, Muito Dificil->Muito Alta.\n"
    "6. Converta R$2.500 para 250000 centavos, R$500 para 50000, R$1.300 para 130000.\n"
    "7. Use somente estes niveis na resposta: Baixa, Media, Alta, Muito Alta ou Insuficiente.\n"
    "8. Responda em uma unica linha, exatamente neste formato:\n"
    "Nivel de dificuldade: <nivel> Preco: <centavos> - Justificativa: <texto curto>\n"
    "9. Nao escreva nada antes ou depois dessa linha.\n\n"
    "Exemplo de conversao:\n"
    "Contexto: DIFICULDADE TECNICA: Dificil | VALOR APROXIMADO: R$2.500 | JUSTIFICATIVA DA DIFICULDADE: desenho complexo\n"
    "Resposta: Nivel de dificuldade: Alta Preco: 250000 - Justificativa: desenho complexo"
)


def ensure_dir(path: str, label: str) -> None:
    if not os.path.isdir(path):
        raise FileNotFoundError(f"O caminho de {label} nao foi encontrado: {path}")


def load_chroma():
    global _chroma_cache

    if _chroma_cache is not None:
        return _chroma_cache

    with _resources_lock:
        if _chroma_cache is not None:
            return _chroma_cache

        ensure_dir(EMBEDDINGS_DIR, "modelo de embeddings")

        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDINGS_DIR
        )
        client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        _chroma_cache = client.get_or_create_collection(
            COLLECTION_NAME,
            embedding_function=embedding_function,
        )
        print("Base vetorial carregada.")
        return _chroma_cache


def load_llm():
    global _llm_cache

    if _llm_cache is not None:
        return _llm_cache

    with _resources_lock:
        if _llm_cache is not None:
            return _llm_cache

        ensure_dir(MODEL_DIR, "modelo principal")

        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            MODEL_DIR,
            local_files_only=True,
            low_cpu_mem_usage=True,
            dtype=torch.float16,
        )

        if torch.cuda.is_available():
            model = model.to("cuda")
            print("Modelo Llama carregado em GPU.")
        else:
            print("Modelo Llama carregado em CPU. A inferencia pode demorar.")

        _llm_cache = (tokenizer, model)
        return _llm_cache


def load_resources():
    collection = load_chroma()
    tokenizer, model = load_llm()
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


def build_prompt(rag_context, user_input, mode="chat", contexto=None):
    system_prompt = SYSTEM_PROMPT_BUDGET if mode == "budget" else SYSTEM_PROMPT_CHAT
    user_suffix = (
        "Com base no contexto, estime a dificuldade e o preco."
        if mode == "budget"
        else "Responda com base no contexto."
    )

    user_parts = [f"Contexto:\n{rag_context}"]
    if contexto:
        user_parts.append(f"Descricao da tatuagem:\n{contexto}")

    user_parts.append(f"Pergunta: {user_input}\n{user_suffix}")

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "\n\n".join(user_parts)},
    ]


def build_response(
    question,
    context,
    tokenizer,
    model,
    mode="chat",
    max_new_tokens=MAX_NEW_TOKENS,
    contexto=None,
):
    truncated_context = truncate_context(context, tokenizer)
    messages = build_prompt(
        truncated_context,
        question,
        mode=mode,
        contexto=contexto,
    )

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
            max_new_tokens=max_new_tokens,
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


def rag_chain(
    question,
    tokenizer,
    model,
    collection,
    n_results=QUERY,
    mode="chat",
    max_new_tokens=MAX_NEW_TOKENS,
    contexto=None,
):
    results = collection.query(
        query_texts=[question],
        n_results=n_results,
    )
    rag_context = "\n\n".join(results["documents"][0]) if results["documents"] else ""
    return build_response(
        question,
        rag_context,
        tokenizer,
        model,
        mode=mode,
        max_new_tokens=max_new_tokens,
        contexto=contexto,
    )


def answer_question(question: str) -> str:
    tokenizer, model, collection = load_resources()
    return rag_chain(question, tokenizer, model, collection)


def build_budget_question(
    cliente,
    tamanho,
    sombreamento,
    colorido,
    estilo,
    area_tatuada,
    regiao_especifica,
    descricao,
) -> str:
    sombra = "com sombreamento" if sombreamento else "sem sombreamento"
    cor = "colorida" if colorido else "sem cor"
    return (
        f"Qual a dificuldade e o preco de uma tatuagem para o cliente {cliente}? "
        f"Descricao: {descricao}. Estilo: {estilo}. Tamanho: {tamanho}. "
        f"Area: {area_tatuada}. Regiao: {regiao_especifica}. {sombra}. Tatuagem {cor}."
    )


def _normalize_difficulty(value: str) -> str:
    cleaned = value.strip()
    aliases = {
        "baixa": "Baixa",
        "facil": "Baixa",
        "fácil": "Baixa",
        "media": "Media",
        "média": "Media",
        "medio": "Media",
        "médio": "Media",
        "alta": "Alta",
        "dificil": "Alta",
        "difícil": "Alta",
        "muito alta": "Muito Alta",
        "muito dificil": "Muito Alta",
        "muito difícil": "Muito Alta",
        "insuficiente": "Insuficiente",
    }
    normalized = aliases.get(cleaned.lower(), cleaned)
    if normalized in DIFFICULTY_LEVELS:
        return normalized
    return "Insuficiente"


def _parse_reais_to_cents(value: str) -> int | None:
    cleaned = re.sub(r"[R$\s]", "", value.strip())
    if not cleaned:
        return None

    if re.fullmatch(r"\d{1,3}(\.\d{3})+", cleaned):
        reais = int(cleaned.replace(".", ""))
    else:
        cleaned = cleaned.replace(",", ".")
        try:
            reais = int(float(cleaned))
        except ValueError:
            return None

    return reais * 100


def parse_budget_analysis(answer: str) -> dict:
    normalized_answer = answer.strip()
    if normalized_answer.lower() in ("nao sei", "não sei"):
        return {
            "estimativaValor": None,
            "dificuldadeIa": "Insuficiente",
            "justificativaIa": "Nao ha informacao suficiente no contexto para estimar o orcamento.",
        }

    dificuldade_match = re.search(
        r"Nivel de dificuldade:\s*(.+?)(?:\s+Preco:|\s*$)",
        normalized_answer,
        re.IGNORECASE,
    )
    preco_match = re.search(r"Preco:\s*(\d+)", normalized_answer, re.IGNORECASE)
    justificativa_match = re.search(
        r"Justificativa:\s*(.+)",
        normalized_answer,
        re.IGNORECASE | re.DOTALL,
    )

    if not dificuldade_match:
        dificuldade_match = re.search(
            r"DIFICULDADE\s*T[EÉ]CNICA:\s*(.+?)(?:\s+VALOR|\s*$)",
            normalized_answer,
            re.IGNORECASE,
        )
    if not preco_match:
        valor_match = re.search(
            r"VALOR\s*APROXIMADO:\s*(R\$?\s*[\d.,]+)",
            normalized_answer,
            re.IGNORECASE,
        )
        estimativa_valor = (
            _parse_reais_to_cents(valor_match.group(1)) if valor_match else None
        )
    else:
        estimativa_valor = int(preco_match.group(1))

    if not justificativa_match:
        justificativa_match = re.search(
            r"JUSTIFICATIVA(?:\s+DA\s+DIFICULDADE)?:\s*(.+)",
            normalized_answer,
            re.IGNORECASE | re.DOTALL,
        )

    dificuldade_ia = (
        _normalize_difficulty(dificuldade_match.group(1))
        if dificuldade_match
        else "Insuficiente"
    )
    justificativa_ia = (
        justificativa_match.group(1).strip()
        if justificativa_match
        else normalized_answer
    )

    if estimativa_valor is None or dificuldade_ia == "Insuficiente":
        return {
            "estimativaValor": estimativa_valor,
            "dificuldadeIa": "Insuficiente",
            "justificativaIa": justificativa_ia or "Resposta da IA fora do formato esperado.",
        }

    return {
        "estimativaValor": estimativa_valor,
        "dificuldadeIa": dificuldade_ia,
        "justificativaIa": justificativa_ia,
    }


def analyze_budget(
    cliente,
    tamanho,
    sombreamento,
    colorido,
    estilo,
    area_tatuada,
    regiao_especifica,
    descricao,
) -> dict:
    question = build_budget_question(
        cliente,
        tamanho,
        sombreamento,
        colorido,
        estilo,
        area_tatuada,
        regiao_especifica,
        descricao,
    )
    tokenizer, model, collection = load_resources()
    answer = rag_chain(
        question,
        tokenizer,
        model,
        collection,
        mode="budget",
        max_new_tokens=MAX_BUDGET_NEW_TOKENS,
    )
    return parse_budget_analysis(answer)
