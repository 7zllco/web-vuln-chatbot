from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st
from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

from src.constants import DEFAULT_OPENAI_MODEL, SOURCE_NAME  # noqa: E402
from src.rag import build_messages, generate_openai_answer  # noqa: E402
from src.retrieval import load_collection, load_embedding_model, rag_retrieve_with_fallback  # noqa: E402


st.set_page_config(
    page_title="웹 취약점 가이드 챗봇",
    page_icon="🔐",
    layout="wide",
)


@st.cache_resource(show_spinner="임베딩 모델을 로드하는 중입니다...")
def get_embedding_model():
    return load_embedding_model()


@st.cache_resource(show_spinner="벡터 DB를 로드하는 중입니다...")
def get_collection():
    return load_collection()


@st.cache_resource(show_spinner=False)
def get_openai_client(api_key: str):
    return OpenAI(api_key=api_key)


def get_secret(name: str, default: str | None = None) -> str | None:
    if name in st.secrets:
        return st.secrets[name]
    return os.getenv(name, default)


with st.sidebar:
    st.title("설정")
    st.caption("KISA 웹 취약점 가이드 기반 RAG 챗봇")

    api_key = get_secret("OPENAI_API_KEY")
    model_name = get_secret("OPENAI_LLM_MODEL", DEFAULT_OPENAI_MODEL)

    st.text_input("OpenAI 모델", value=model_name, key="openai_model_name")
    top_k_note = st.caption("검색 top-k는 라우팅 결과에 따라 자동 조정됩니다.")

    show_sources = st.toggle("검색 근거 보기", value=True)
    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.rerun()

st.title("🔐 웹 취약점 가이드 챗봇")
st.caption(f"기반 문서: {SOURCE_NAME}")

if not api_key:
    st.error(
        "OPENAI_API_KEY가 설정되어 있지 않습니다. Streamlit Cloud의 App settings > Secrets에 "
        "OPENAI_API_KEY를 등록해주세요."
    )
    st.stop()

try:
    embedding_model = get_embedding_model()
    collection = get_collection()
except Exception as exc:
    st.error("앱 초기화에 실패했습니다.")
    st.exception(exc)
    st.info(
        "data/chroma_db 폴더가 프로젝트에 포함되어 있는지 확인하세요. "
        "없다면 scripts/build_chroma_from_embeddings.py로 먼저 생성해야 합니다."
    )
    st.stop()

client = get_openai_client(api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources") and show_sources:
            with st.expander("검색 근거"):
                for source in message["sources"]:
                    st.markdown(source)

user_query = st.chat_input("예: SQL 인젝션 조치 방법 알려줘")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("문서 검색 및 답변 생성 중..."):
            route, results = rag_retrieve_with_fallback(user_query, embedding_model, collection)
            messages = build_messages(user_query, route, results)
            answer = generate_openai_answer(
                client=client,
                messages=messages,
                model_name=st.session_state.openai_model_name,
            )

        st.markdown(answer)

        source_blocks = []
        if results.get("documents"):
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]
            for i, (doc, meta, distance) in enumerate(zip(docs, metas, distances), start=1):
                source = (
                    f"**근거 {i}**  \n"
                    f"- 출처: {meta.get('chapter', '')} > {meta.get('item_title', '')}"
                    f"({meta.get('item_code', '')}) > {meta.get('section', '')}  \n"
                    f"- 거리: `{distance:.4f}`  \n\n"
                    f"> {doc[:500].replace(chr(10), ' ')}..."
                )
                source_blocks.append(source)

        if show_sources and source_blocks:
            with st.expander("검색 근거"):
                for source in source_blocks:
                    st.markdown(source)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": source_blocks, "route": route}
    )
