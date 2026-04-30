from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
CHROMA_PATH = DATA_DIR / "chroma_db"
COLLECTION_NAME = "kisa_web_vulnerability_guide_bge_m3"
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"

SOURCE_NAME = "주요정보통신기반시설 기술적 취약점 분석, 평가 방법 상세가이드(웹).pdf"
