from __future__ import annotations

from typing import Any

ITEM_ALIASES = {
    "SQL 인젝션": {"item_code": "SI", "keywords": ["sql 인젝션", "sql injection", "sqli"]},
    "코드 인젝션": {"item_code": "CI", "keywords": ["코드 인젝션", "code injection", "명령 실행", "os command", "ldap", "xpath", "xxe", "ssti"]},
    "디렉터리 인덱싱": {"item_code": "DI", "keywords": ["디렉터리 인덱싱", "directory indexing", "디렉토리 인덱싱"]},
    "에러 페이지 적용 미흡": {"item_code": "EP", "keywords": ["에러 페이지", "오류 페이지", "error page"]},
    "정보 누출": {"item_code": "IL", "keywords": ["정보 누출", "정보 노출", "information leakage", "마스킹"]},
    "크로스사이트 스크립트": {"item_code": "XS", "keywords": ["xss", "크로스사이트 스크립트", "크로스사이트 스크립팅", "스크립팅"]},
    "크로스사이트 요청 위조": {"item_code": "CF", "keywords": ["csrf", "크로스사이트 요청 위조"]},
    "서버사이드 요청 위조": {"item_code": "SF", "keywords": ["ssrf", "서버사이드 요청 위조", "server side request forgery"]},
    "약한 비밀번호 정책": {"item_code": "BF", "keywords": ["약한 비밀번호", "비밀번호 정책", "패스워드 정책"]},
    "불충분한 인증 절차": {"item_code": "IA", "keywords": ["불충분한 인증", "인증 절차", "재인증", "본인인증"]},
    "불충분한 권한 검증": {"item_code": "IN", "keywords": ["권한 검증", "접근 권한", "인가", "권한 우회"]},
    "취약한 비밀번호 복구 절차": {"item_code": "PR", "keywords": ["비밀번호 복구", "비밀번호 찾기", "password recovery"]},
    "프로세스 검증 누락": {"item_code": "PV", "keywords": ["프로세스 검증", "검증 누락", "절차 우회"]},
    "악성 파일 업로드": {"item_code": "FU", "keywords": ["파일 업로드", "악성 파일 업로드", "업로드 취약점"]},
    "파일 다운로드": {"item_code": "FD", "keywords": ["파일 다운로드", "다운로드 취약점", "경로 조작"]},
    "불충분한 세션 관리": {"item_code": "IS", "keywords": ["세션 관리", "세션 고정", "session"]},
    "데이터 평문 전송": {"item_code": "SN", "keywords": ["평문 전송", "https", "암호화 전송", "ssl", "tls"]},
    "쿠키 변조": {"item_code": "CC", "keywords": ["쿠키 변조", "cookie"]},
    "관리자 페이지 노출": {"item_code": "AE", "keywords": ["관리자 페이지", "admin page", "관리자 페이지 노출"]},
    "자동화 공격": {"item_code": "AU", "keywords": ["자동화 공격", "captcha", "봇", "무차별 대입"]},
    "불필요한 Method 악용": {"item_code": "WM", "keywords": ["method", "http method", "불필요한 method", "options", "put", "delete"]},
}

SECTION_ALIASES = {
    "개요": ["개요", "설명", "정의", "뭐야", "무엇", "개념"],
    "점검 내용": ["점검 내용", "무엇을 점검"],
    "점검 목적": ["점검 목적", "목적", "왜 점검"],
    "보안 위협": ["보안 위협", "위협", "위험", "영향", "공격 가능"],
    "판단 기준": ["판단 기준", "양호", "취약", "기준"],
    "조치 방법": ["조치 방법", "대응", "해결", "방어", "막는 법", "예방", "보완", "수정", "권고"],
    "점검 및 조치 사례": ["점검 방법", "점검 사례", "조치 사례", "테스트", "확인 방법", "진단"],
}


def detect_item(query: str) -> dict[str, str] | None:
    q = query.lower()
    for item_title, info in ITEM_ALIASES.items():
        for keyword in info["keywords"]:
            if keyword.lower() in q:
                return {"item_title": item_title, "item_code": info["item_code"]}
    return None


def detect_section(query: str) -> str | None:
    q = query.lower()
    for section, keywords in SECTION_ALIASES.items():
        for keyword in keywords:
            if keyword.lower() in q:
                return section
    return None


def detect_intent(query: str) -> str:
    q = query.lower()
    if any(x in q for x in ["조치", "대응", "해결", "방어", "막는", "예방", "수정", "권고"]):
        return "remediation"
    if any(x in q for x in ["점검", "진단", "확인", "테스트", "검사"]):
        return "assessment"
    if any(x in q for x in ["기준", "양호", "취약", "판단"]):
        return "criteria"
    if any(x in q for x in ["위협", "위험", "영향", "공격"]):
        return "threat"
    if any(x in q for x in ["뭐야", "무엇", "설명", "개념", "정의"]):
        return "definition"
    return "general"


def build_chroma_where(item: dict[str, str] | None, section: str | None) -> dict[str, Any] | None:
    filters: list[dict[str, str]] = []
    if item:
        filters.append({"item_code": item["item_code"]})
    if section:
        filters.append({"section": section})
    if not filters:
        return None
    if len(filters) == 1:
        return filters[0]
    return {"$and": filters}


def route_query(query: str) -> dict[str, Any]:
    item = detect_item(query)
    section = detect_section(query)
    intent = detect_intent(query)

    if section is None:
        if intent == "remediation":
            section = "조치 방법"
        elif intent == "assessment":
            section = "점검 및 조치 사례"
        elif intent == "criteria":
            section = "판단 기준"
        elif intent == "threat":
            section = "보안 위협"
        elif intent == "definition":
            section = "개요"

    where = build_chroma_where(item, section)
    n_results = 5 if item and section else 8 if item else 10

    return {
        "query": query,
        "intent": intent,
        "item": item,
        "section": section,
        "where": where,
        "n_results": n_results,
        "fallback": False,
    }
