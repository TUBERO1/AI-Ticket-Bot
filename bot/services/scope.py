import re

GREETING_ONLY = re.compile(
    r"^(hi|hello|hey|yo|sup|thanks|thank\s*you|thx|안녕하세요|안녕|하이|헬로)[\s!.?~ㅋㅎ]*$",
    re.I,
)

SCOPE_REPLY = (
    "Please describe your issue a bit more clearly.\n"
    "You can also use Call Staff in the ticket if you need a human."
)

GREETING_REPLY = "Hi. Send your question and I will help."


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
