from __future__ import annotations

from typing import Any

from openai import OpenAI

from .constants import DEFAULT_OPENAI_MODEL


def format_context(results: dict[str, Any], max_docs: int = 5, max_chars_per_doc: int = 1600) -> str:
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    blocks: list[str] = []
    for i, (doc, meta, distance) in enumerate(zip(docs, metas, distances), start=1):
        source = (
            f"{meta.get('chapter', '')} > "
            f"{meta.get('item_title', '')}({meta.get('item_code', '')}) > "
            f"{meta.get('section', '')}"
        )
        blocks.append(
            f"""[근거 {i}]
출처: {source}
거리: {distance}

{doc[:max_chars_per_doc]}""".strip()
        )
        if i >= max_docs:
            break

    return "\n\n".join(blocks)


def build_messages(query: str, route: dict[str, Any], results: dict[str, Any]) -> list[dict[str, str]]:
    context = format_context(results)

    system_prompt = """
너는 한국어 보안 가이드 문서를 기반으로 답변하는 RAG 챗봇이다.

규칙:
- 반드시 제공된 근거 안에서만 답변한다.
- 근거에 없는 내용은 추측하지 않는다.
- 근거가 부족하면 "제공된 문서 근거만으로는 확인할 수 없습니다."라고 답한다.
- 답변은 한국어로 한다.
- 가능하면 항목명, 항목코드, 섹션명을 함께 언급한다.
- 조치 방법이나 점검 방법은 단계적으로 정리한다.
- 답변 마지막에 참고한 근거 번호를 적는다.
""".strip()

    user_prompt = f"""
질문:
{query}

라우팅 정보:
- intent: {route.get('intent')}
- item: {route.get('item')}
- section: {route.get('section')}
- fallback: {route.get('fallback')}

검색된 근거:
{context}
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def generate_openai_answer(
    client: OpenAI,
    messages: list[dict[str, str]],
    model_name: str = DEFAULT_OPENAI_MODEL,
) -> str:
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()
