from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(r"C:\Users\HORIZON\Manuals Automation Chatbot")
SOP_DIR = BASE_DIR / "manuals"
DB_DIR = BASE_DIR / "weaviate_store"

SOP_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

class Config:
    MODEL = "gpt-4o"
    EMBED_MODEL = "text-embedding-3-large"
    INDEX_NAME = "EnterpriseSops"