import os
import chromadb
from chromadb.utils import embedding_functions
import dotenv

dotenv.load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
EMBEDDINGS_DIR = os.getenv("EMBEDDINGS_DIR", os.path.join(BASE_DIR, "embeddings"))
CHROMADB_DIR = os.path.join(BASE_DIR, "chroma_db")

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "dataset_collection")
SOURCE_DATA_PATH = os.getenv("SOURCE_DATA_PATH", os.path.join(BASE_DIR, "source_data.txt"))

def ensure_local_path(path: str, label: str) -> None:
    if not os.path.isdir(path):
        raise FileNotFoundError(f"O caminho de {label} nao foi encontrado: {path}")


def parse_faq_entries(text: str):
    entries = []
    current_question = None
    current_answer_lines = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.upper().startswith("FAQ"):
            continue

        if line.endswith("?"):
            if current_question and current_answer_lines:
                answer = " ".join(current_answer_lines).strip()
                entries.append(
                    {
                        "question": current_question,
                        "answer": answer,
                        "document": f"passage: {current_question}\n{answer}",
                    }
                )
            current_question = line
            current_answer_lines = []
        elif current_question:
            current_answer_lines.append(line)

    if current_question and current_answer_lines:
        answer = " ".join(current_answer_lines).strip()
        entries.append(
            {
                "question": current_question,
                "answer": answer,
                "document": f"passage: {current_question}\n{answer}",
            }
        )

    return entries


ensure_local_path(EMBEDDINGS_DIR, "modelo de embeddings")

huggingface_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDINGS_DIR
)

client = chromadb.PersistentClient(path=CHROMADB_DIR)

try:
    client.delete_collection(COLLECTION_NAME)
except Exception:
    pass

collection = client.get_or_create_collection(
    COLLECTION_NAME,
    embedding_function=huggingface_ef,
)

with open(SOURCE_DATA_PATH, "r", encoding="utf-8") as file:
    books = file.read()

entries = parse_faq_entries(books)

for i, entry in enumerate(entries):
    collection.add(
        documents=[entry["document"]],
        ids=[str(i)],
        metadatas=[{"question": entry["question"]}],
    )

print(f"{len(entries)} entradas adicionadas na colecao {COLLECTION_NAME}.")