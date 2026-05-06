import os 
import sys
from dotenv import load_dotenv
from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer


load_dotenv()
hf_token = os.getenv("HF_TOKEN", "").strip()

llm_model_name = "meta-llama/Llama-3.2-3B-Instruct"
embedding_model_name = "intfloat/multilingual-e5-small"

llm_path = "./models/llama-3.2-3b-instruct"
embedding_path = "./models/multilingual-e5-small"


def download_model():
    if not hf_token:
        print("HF_TOKEN is not set. Please set it in the .env file.")
        return
    
    if os.path.exists(llm_path) or os.path.exists(embedding_path):
        print("Models already exist. Skipping download.")
        return

    try:
        snapshot_download(repo_id=llm_model_name, local_dir=llm_path, token=hf_token)
        embedding_model = SentenceTransformer(embedding_model_name)    
    except Exception as e:
        print(f"Error downloading models: {e}")
        sys.exit(1)

    embedding_model.save(embedding_path)

    print("Models downloaded and saved successfully.")

if __name__ == "__main__":
    download_model()
