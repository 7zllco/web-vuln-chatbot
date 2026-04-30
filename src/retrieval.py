from __future__ import annotations

from typing import Any

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from .constants import CHROMA_PATH, COLLECTION_NAME, EMBEDDING_MODEL_NAME
from .routing import route_query


def load_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL_NAME, device="cpu")


def load_collection():
    if not CHROMA_PATH.exists():
        raise FileNotFoundError(
            f"ChromaDB 경로가 없습니다: {CHROMA_PATH}. "
            "scripts/build_chroma_from_embeddings.py로 data/chroma_db를 먼저 생성하거나, "
            "기존 chroma_db 폴더를 data/chroma_db에 넣어주세요."
        )

    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_collection(COLLECTION_NAME)


def dense_search(
    query: str,
    embedding_model: SentenceTransformer,
    collection,
    n_results: int = 5,
    where: dict[str, Any] | None = None,
):
    query_embedding = embedding_model.encode([query], normalize_embeddings=True)[0].tolist()

    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if where is not None:
        kwargs["where"] = where

    return collection.query(**kwargs)


def routed_dense_search(query: str, embedding_model: SentenceTransformer, collection):
    route = route_query(query)
    results = dense_search(
        query=query,
        embedding_model=embedding_model,
        collection=collection,
        n_results=route["n_results"],
        where=route["where"],
    )
    return route, results


def rag_retrieve_with_fallback(query: str, embedding_model: SentenceTransformer, collection):
    route, results = routed_dense_search(query, embedding_model, collection)
    has_result = bool(results.get("documents") and results["documents"][0])

    if has_result:
        return route, results

    fallback_results = dense_search(
        query=query,
        embedding_model=embedding_model,
        collection=collection,
        n_results=10,
        where=None,
    )
    route["fallback"] = True
    route["where"] = None
    return route, fallback_results
