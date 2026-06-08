import os 
import sys
from dotenv import load_dotenv
from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer


load_dotenv()
# Define paths and model names
hf_token = os.getenv("HF_TOKEN", "").strip()

llm_model_name = "meta-llama/Llama-3.2-1B-Instruct"
embedding_model_name = "intfloat/multilingual-e5-small"

llm_path = os.getenv("MODEL_DIR", "./models/llama-3.2-1b-instruct")
embedding_path = os.getenv("EMBEDDINGS_DIR", "./models/multilingual-e5-small")


def download_model():
    if not hf_token:
        print("HF_TOKEN is not set. Please set it in the .env file.")
        return

    need_llm = not os.path.exists(llm_path)
    need_embeddings = not os.path.exists(embedding_path)

    if not need_llm and not need_embeddings:
        print("Models already exist. Skipping download.")
        return

    try:
        if need_llm:
            print(f"Baixando LLM {llm_model_name}...")
            snapshot_download(repo_id=llm_model_name, local_dir=llm_path, token=hf_token)
        if need_embeddings:
            print(f"Baixando embeddings {embedding_model_name}...")
            embedding_model = SentenceTransformer(embedding_model_name)
            embedding_model.save(embedding_path)
    except Exception as e:
        print(f"Error downloading models: {e}")
        sys.exit(1)

    print("Models downloaded and saved successfully.")

if __name__ == "__main__":
    download_model()
