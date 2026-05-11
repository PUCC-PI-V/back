import os
from dotenv import load_dotenv
from utils.installModels.installModels import download_model
from database.vectorDatabase.downloadDatas import download_datas


load_dotenv()

EMBEDDINGS_DIR = os.getenv("EMBEDDINGS_DIR", os.path.join(os.path.dirname(__file__), "models/multilingual-e5-small"))
MODEL_DIR = os.getenv("MODEL_DIR", os.path.join(os.path.dirname(__file__), "models/llama-3.2-3b-instruct"))
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", os.path.join(os.path.dirname(__file__), "database/vectorDatabase/chroma_db"))

def autoInstallModels():
    if not os.path.exists(EMBEDDINGS_DIR) or not os.path.exists(MODEL_DIR):
        download_model()
    else:
        print("Models already installed")

    if not os.path.exists(CHROMA_DB_DIR):
        download_datas()
    else:
        print("ChromaDB already installed")