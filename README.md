# web-vuln-chatbot

KISA 웹 취약점 가이드 기반 Streamlit RAG 챗봇입니다.

## 프로젝트 구조

```text
web-vuln-chatbot/
├── streamlit_app.py
├── requirements.txt
├── src/
│   ├── constants.py
│   ├── routing.py
│   ├── retrieval.py
│   └── rag.py
├── scripts/
│   └── build_chroma_from_embeddings.py
├── data/
│   └── chroma_db/  # 생성 후 배치
└── .streamlit/
    └── secrets.toml.example
```

## 배포 전 준비

Colab에서 만든 `kisa_web_vulnerability_embeddings_bge_m3.jsonl` 파일이 있다면 다음 명령으로 ChromaDB를 생성합니다.

```bash
python scripts/build_chroma_from_embeddings.py \
  --embeddings data/kisa_web_vulnerability_embeddings_bge_m3.jsonl
```

생성된 `data/chroma_db` 폴더를 프로젝트에 포함해야 Streamlit Cloud에서 검색이 동작합니다.

## Streamlit Secrets

Streamlit Cloud의 **App settings > Secrets**에 아래 값을 등록하세요.

```toml
OPENAI_API_KEY = "sk-..."
OPENAI_LLM_MODEL = "gpt-4o-mini"
```

API 키를 코드에 직접 하드코딩하지 마세요.

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 정리 내용

Colab 노트북에서 다음 요소는 배포용 코드에서 제거했습니다.

- `drive.mount()`
- `!pip install` 셀
- Docling PDF 파싱 셀
- 청킹/임베딩 생성 셀
- 테스트용 출력 셀
- 하드코딩된 API 키

앱은 이미 생성된 ChromaDB를 로드하고, 질문 시 BGE-M3로 query embedding을 만든 뒤 OpenAI Chat Completions로 답변을 생성합니다.
