import re

from bot.guild_config import MODE_LUMENTIA, MODE_RFIVEM

LUMENTIA_SCOPE_REPLY = (
    "Lumentia **외주·견적·서비스·등급·진행 방식** 관련만 안내해 드릴 수 있어요.\n"
    "웹·봇·플러그인 제작이나 가격 문의를 적어 주세요."
)

RFIVEM_SCOPE_REPLY = (
    "RFIVEM **법전·RP 판별·서버 규칙·용어** 관련만 안내해 드릴 수 있어요.\n"
    "RP 상황이나 용어를 구체적으로 적어 주세요."
)

GREETING_ONLY = re.compile(
    r"^(안녕|안녕하세요|안뇽|안뇽하세요|하이|헬로|hello|hi|hey|반가|감사|고마|thanks|thank\s*you)[\s!.?~ㅋㅎ]*$",
    re.I,
)

LUMENTIA_IN_SCOPE = [
    r"lumentia", r"루멘티아", r"외주", r"견적", r"가격", r"비용", r"얼마", r"제작", r"개발",
    r"의뢰", r"문의", r"구매", r"주문", r"티켓", r"봇", r"플러그인", r"웹", r"사이트", r"랜딩",
    r"마인크래프트", r"마크", r"로블록스", r"roblox", r"api", r"백엔드", r"db", r"유지보수",
    r"환불", r"등급", r"vip", r"할인", r"혜택", r"호스팅", r"납품", r"진행", r"결제", r"상담",
    r"사업자", r"lumentia\.co\.kr", r"수정", r"납기", r"기간", r"일정", r"며칠", r"취약점", r"보안",
    r"만들어", r"해줘", r"해주", r"가능", r"서비스", r"기능", r"제작", r"개발",
    r"슬래시", r"slash", r"패널", r"티켓봇", r"자동화", r"쇼핑몰", r"대시보드",
    r"관리자\s*페이지", r"결제\s*연동", r"포트폴리오", r"앱", r"모바일",
    r"챗봇", r"chatbot", r"사업체", r"등록", r"디코",
]

LUMENTIA_SERVICE_INTENT = [
    r"만들", r"제작", r"개발", r"의뢰", r"주문", r"해줘", r"해주", r"부탁",
    r"봇", r"웹", r"사이트", r"플러그인", r"로블록스", r"마인크래프트", r"마크",
]

LUMENTIA_OFFTOPIC = [
    r"유튜브", r"youtube", r"유머", r"재미\s*있", r"콘텐츠\s*추천", r"채널\s*추천",
    r"영화", r"드라마", r"넷플릭스", r"netflix", r"노래\s*추천", r"음악\s*추천",
    r"게임\s*추천", r"날씨", r"주식", r"코인", r"뉴스", r"번역\s*해", r"영어로\s*말",
    r"파이썬\s*코드", r"코드\s*짜", r"코드\s*작성", r"코드\s*만들", r"프로그램\s*짜",
    r"스크립트\s*짜", r"알고리즘", r"숙제", r"레시피", r"요리\s*법", r"연애\s*상담",
    r"심리\s*상담", r"정치", r"선거", r"의료\s*상담", r"투자\s*조언",
]

RFIVEM_IN_SCOPE = [
    r"rfivem", r"fivem", r"파이브", r"rp", r"알피", r"역할", r"논알피", r"non\s*rp", r"배드",
    r"bad\s*rp", r"파워", r"메타", r"이중", r"rdm", r"vdm", r"ooc", r"ic", r"법전", r"법률",
    r"형법", r"조항", r"제\d+조", r"판별", r"판정", r"체포", r"구금", r"벌금", r"보호구역",
    r"팩션", r"스토리", r"필드", r"도주", r"추격", r"수배", r"강도", r"납치", r"전투",
    r"스태프", r"운영", r"제재", r"신고", r"증거", r"총기", r"ems", r"보안국", r"렉카",
]

RFIVEM_OFFTOPIC = [
    r"유튜브", r"youtube", r"유머", r"재미\s*있", r"콘텐츠\s*추천", r"채널\s*추천",
    r"영화", r"드라마", r"외주", r"견적", r"루멘티아", r"lumentia", r"파이썬\s*코드",
    r"코드\s*짜", r"번역", r"날씨", r"주식", r"레시피", r"게임\s*추천",
]

BAD_OUTPUT_MARKERS = [
    r"유튜브", r"youtube", r"검색창에서", r"추천해\s*드릴", r"인기\s*있는\s*.*채널",
    r"here are", r"i recommend", r"you can try", r"feel free to", r"let me know if",
    r"재미있는\s*콘텐츠", r"유머\s*채널", r"comedy", r"piper\s*chapman",
    r"도와드릴\s*일이\s*무엇인지\s*자세히", r"웹사이트\s*제작이나\s*디스코드\s*봇\s*개발\s*등\s*구체적인\s*요구사항",
    r"구체적인\s*요구사항을\s*말씀", r"자세히\s*알려\s*주시", r"무엇을\s*도와드릴",
    r"feel\s+free\s+to\s+ask", r"happy\s+to\s+help",
]

LUMENTIA_WEAK_OUTPUT = [
    r"구체적인\s*요구사항",
    r"자세히\s*알려",
    r"도와드릴\s*일",
    r"무엇을\s*도와",
    r"편하게\s*물어보",
]

ALLOWED_LATIN = {
    "rp", "non-rp", "bad", "rdm", "vdm", "ooc", "ic", "ems", "rfivem", "fivem",
    "vip", "vvip", "mvip", "svip", "lumentia", "api", "db", "discord",
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _hit(text: str, patterns: list[str]) -> bool:
    t = _norm(text)
    return any(re.search(p, t, re.I) for p in patterns)


def scope_reply(server_mode: str) -> str:
    if server_mode == MODE_RFIVEM:
        return RFIVEM_SCOPE_REPLY
    return LUMENTIA_SCOPE_REPLY


def greeting_reply(server_mode: str) -> str:
    if server_mode == MODE_RFIVEM:
        return (
            "안녕하세요! RFIVEM 법률·RP 판별 AI입니다.\n"
            "RP 상황이나 용어(배드 알피, 이중 RP 등)를 적어 주세요."
        )
    return (
        "안녕하세요! **Lumentia** 외주 문의 AI입니다.\n"
        "봇·웹·플러그인 제작, **견적·기간·등급·진행방식** 질문을 적어 주세요.\n"
        "예: 「티켓 봇 견적」, 「웹사이트 얼마에 몇 일」"
    )


def is_greeting_only(text: str) -> bool:
    if not text or not text.strip():
        return False
    return bool(GREETING_ONLY.match(_norm(text)))


def is_in_scope(text: str, server_mode: str) -> bool:
    if not text or not text.strip():
        return False

    if is_greeting_only(text):
        return True

    if server_mode == MODE_RFIVEM:
        if _hit(text, RFIVEM_IN_SCOPE):
            return True
        if _hit(text, RFIVEM_OFFTOPIC):
            return False
        return len(_norm(text)) <= 8

    if _hit(text, LUMENTIA_IN_SCOPE):
        return True
    if _hit(text, LUMENTIA_SERVICE_INTENT) and not _hit(text, LUMENTIA_OFFTOPIC):
        return True
    if _hit(text, LUMENTIA_OFFTOPIC):
        return False
    return len(_norm(text)) <= 8


def is_non_korean_output(text: str) -> bool:
    if not text or len(text.strip()) < 8:
        return False

    hangul = len(re.findall(r"[가-힣]", text))
    latin_words = re.findall(r"[a-zA-Z]{4,}", text)
    latin_chars = sum(len(w) for w in latin_words)

    if hangul == 0 and latin_chars > 10:
        return True

    if hangul + latin_chars == 0:
        return False

    ratio = hangul / (hangul + latin_chars)
    if ratio < 0.35 and latin_chars > 15:
        return True

    if re.search(r"(?:[a-zA-Z]{4,}\s+){4,}", text) and ratio < 0.5:
        filtered = text.lower()
        for word in ALLOWED_LATIN:
            filtered = filtered.replace(word, "")
        if len(re.findall(r"[a-zA-Z]{4,}", filtered)) >= 3:
            return True

    return False


def is_offtopic_output(text: str, server_mode: str) -> bool:
    if not text:
        return True

    if _hit(text, BAD_OUTPUT_MARKERS):
        return True

    if server_mode == MODE_LUMENTIA:
        if _hit(text, LUMENTIA_OFFTOPIC) and not _hit(text, LUMENTIA_IN_SCOPE):
            return True
        if re.search(r"\d+\.\s*\*\*", text) and _hit(text, [r"추천", r"채널", r"유튜브"]):
            return True
        if _hit(text, LUMENTIA_WEAK_OUTPUT) and not _hit(text, LUMENTIA_IN_SCOPE):
            if not re.search(r"\d+[,\d]*\s*원|만원|\d+~\d+일", text):
                return True

    if server_mode == MODE_RFIVEM:
        has_verdict = "판정:" in text or "**판정:**" in text
        if _hit(text, RFIVEM_OFFTOPIC) and not has_verdict and not _hit(text, RFIVEM_IN_SCOPE):
            return True
        if _hit(text, [r"외주", r"루멘티아", r"lumentia", r"견적"]) and not has_verdict:
            return True

    return False
