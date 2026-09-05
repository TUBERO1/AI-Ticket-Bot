import re

GREETING_ONLY = re.compile(
    r"^(안녕|안녕하세요|안뇽|안뇽하세요|하이|헬로|hello|hi|hey|반가|감사|고마|thanks|thank\s*you)[\s!.?~ㅋㅎ]*$",
    re.I,
)

SCOPE_REPLY = (
    "문의 내용을 조금 더 구체적으로 적어 주세요.\n"
    "필요하면 티켓에서 관리자 호출을 눌러 주세요."
)

GREETING_REPLY = "안녕하세요. 문의 내용을 남겨 주시면 바로 도와드릴게요."


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def scope_reply() -> str:
    return SCOPE_REPLY


def greeting_reply() -> str:
    return GREETING_REPLY


def is_greeting_only(text: str) -> bool:
    if not text or not text.strip():
        return False
    return bool(GREETING_ONLY.match(_norm(text)))
