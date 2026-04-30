"""Build ChromaDB from a precomputed BGE-M3 embeddings JSONL file.

Expected JSONL record format:
{
  "text": "...",
  "metadata": {...},
  "embedding_model": "BAAI/bge-m3",
  "embedding": [0.1, ...]
}

Usage:
  python scripts/build_chroma_from_embeddings.py \
    --embeddings data/kisa_web_vulnerability_embeddings_bge_m3.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import chromadb
from chromadb.config import Settings
from tqdm import tqdm

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CHROMA_PATH = ROOT_DIR / "data" / "chroma_db"
COLLECTION_NAME = "kisa_web_vulnerability_guide_bge_m3"
MODEL_NAME = "BAAI/bge-m3"


def make_record_id(record: dict) -> str:
    raw = json.dumps(
        {
            "text": record["text"],
            "metadata": record["metadata"],
            "embedding_model": record.get("embedding_model", MODEL_NAME),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--embeddings", required=True, help="Path to embeddings JSONL file")
    parser.add_argument("--chroma-path", default=str(DEFAULT_CHROMA_PATH), help="Output ChromaDB path")
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()

    embeddings_path = Path(args.embeddings)
    chroma_path = Path(args.chroma_path)
    chroma_path.parent.mkdir(parents=True, exist_ok=True)

    records = list(iter_jsonl(embeddings_path))
    if not records:
        raise ValueError(f"No records found: {embeddings_path}")

    client = chromadb.PersistentClient(
        path=str(chroma_path),
        settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "KISA 웹 취약점 가이드 - BAAI/bge-m3 embeddings",
            "embedding_model": MODEL_NAME,
            "hnsw:space": "cosine",
        },
    )

    for start in tqdm(range(0, len(records), args.batch_size)):
        batch = records[start : start + args.batch_size]
        collection.upsert(
            ids=[make_record_id(r) for r in batch],
            documents=[r["text"] for r in batch],
            metadatas=[r["metadata"] for r in batch],
            embeddings=[r["embedding"] for r in batch],
        )

    print("ChromaDB build complete")
    print("path:", chroma_path)
    print("collection:", COLLECTION_NAME)
    print("count:", collection.count())


if __name__ == "__main__":
    main()
