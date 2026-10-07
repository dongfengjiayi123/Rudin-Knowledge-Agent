from pathlib import Path
import os
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', override=False)

def path_env(name: str, default: str) -> Path:
    p = Path(os.getenv(name) or default)
    return p if p.is_absolute() else ROOT / p

DB_PATH = path_env('RUDIN_DB', 'data/knowledge.db')
PDF_PATH = path_env('RUDIN_PDF', 'data/books/rudin.pdf')
