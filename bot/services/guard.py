import re
import unicodedata

INJECTION_REPLY = (
    "I can't process that request.\n"
    "Please send a normal support question, or use Call Staff if you need a human."
)

ZERO_WIDTH = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]")

HARD_PATTERNS = [
    r"프롬프트?\s*(를|을|만)?\s*무시",
    r"프롬포트?\s*(를|을|만)?\s*무시",
    r"프롬프트?\s*출력",
    r"프롬프트?\s*보여",
    r"프롬프트?\s*알려",
    r"시스템\s*프롬프트",
    r"시스템\s*메시지",
    r"시스템\s*지시",
    r"지시\s*(를|을|만)?\s*무시",
    r"명령\s*(를|을|만)?\s*무시",
    r"규칙\s*(를|을|만)?\s*무시",
    r"이전\s*(지시|명령|규칙|대화|맥락)\s*무시",
    r"위\s*(지시|명령|규칙)\s*무시",
    r"ignore\s+(all\s+)?(previous\s+)?(prompts?|instructions?|rules?|context)",
    r"disregard\s+(all\s+)?(previous\s+)?(prompts?|instructions?|rules?)",
    r"forget\s+(all\s+)?(previous\s+)?(prompts?|instructions?|rules?)",
    r"override\s+(the\s+)?(system|instructions?|rules?)",
    r"bypass\s+(the\s+)?(filter|safety|rules?|restrictions?)",
    r"jailbreak",
    r"prompt\s*injection",
    r"탈옥",
    r"우회\s*(해|하|해서|하라|해봐|가능)",
    r"필터\s*우회",
    r"안전\s*장치\s*끄",
    r"제한\s*해제",
    r"dan\s*mode",
    r"developer\s*mode",
    r"dev\s*mode",
    r"sudo\s*mode",
    r"unrestricted\s*mode",
    r"do\s+anything\s+now",
    r"you\s+are\s+now\s+",
    r"from\s+now\s+on\s+you",
    r"pretend\s+(you\s+are|to\s+be)",
    r"act\s+as\s+(if\s+)?(you\s+have\s+no|there\s+are\s+no)",
    r"role\s*play\s+as",
    r"simulate\s+(being|a)\s+",
    r"가장\s*(해서|하라|해봐|해줘)",
    r"역할\s*(을|를)?\s*(바꿔|변경|전환|바꿔서)",
    r"너는\s*이제\s+",
    r"너의\s*역할은\s*이제",
    r"새로운\s*(지시|명령|규칙|역할)",
    r"비밀\s*지시",
    r"숨겨진\s*지시",
    r"진짜\s*지시",
    r"실제\s*지시",
    r"내부\s*지시",
    r"original\s*instructions?",
    r"hidden\s*instructions?",
    r"secret\s*instructions?",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"show\s+(me\s+)?(your\s+)?(system\s+)?prompt",
    r"print\s+(your\s+)?(system\s+)?prompt",
    r"repeat\s+(the\s+)?(system\s+)?(prompt|instructions?)",
    r"그대로\s*따라",
    r"그대로\s*반복",
    r"echo\s+",
    r"say\s+only\s+",
    r"respond\s+only\s+with",
    r"output\s+only\s+",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"\[INST\]",
    r"\[/INST\]",
    r"<<SYS>>",
    r"<</SYS>>",
    r"###\s*system",
    r"###\s*instruction",
    r"base64\s*decode",
    r"eval\s*\(",
    r"exec\s*\(",
    r"os\.system",
    r"subprocess",
    r"rm\s+-rf",
    r"해킹",
    r"크랙",
    r"악성\s*코드",
    r"랜섬웨어",
    r"피싱\s*사이트",
    r"가짜\s*로그인",
    r"@\s*everyone",
    r"@\s*here",
    r"everyone\s*멘션",
    r"here\s*멘션",
    r"모두\s*멘션",
    r"전체\s*멘션",
]

SOFT_KEYWORDS = [
    "무시", "ignore", "forget", "override", "bypass", "jailbreak", "탈옥", "우회",
    "프롬프트", "프롬포트", "prompt", "instruction", "system", "시스템",
    "역할", "roleplay", "pretend", "act as", "가장", "simulate",
    "developer", "unrestricted", "제한없", "필터", "안전장치",
    "출력만", "only say", "only output", "repeat after", "그대로",
    "비밀", "secret", "hidden", "reveal", "leak", "노출",
    "dan", "sudo", "dev mode", "새 규칙", "new rule",
    "토큰", "api key", "api키", "비밀번호 알려",
]

LEGIT_KEYWORDS = [
    "문의", "티켓", "도움", "질문", "신고", "환불", "결제", "계정",
    "서버", "역할", "채널", "봇", "설정", "오류", "버그", "접속",
    "관리자", "스태프", "운영", "규칙", "가이드", "이용", "가입",
]

OUTPUT_LEAK_PATTERNS = [
    r"프롬프트?\s*(는|은)\s*",
    r"시스템\s*지시",
    r"my\s+system\s+prompt",
    r"my\s+instructions?\s+are",
    r"jailbreak\s+successful",
    r"제한을\s*해제",
    r"역할을\s*변경했",
    r"이제\s*제한\s*없",
]

SIMPLE_COMPLIANCE = {
    "안녕", "안녕!", "안녕.", "hello", "hello!", "hi", "hi!",
    "네", "예", "ok", "okay", "알겠습니다",
}


def _strip_noise(text: str) -> str:
    text = ZERO_WIDTH.sub("", text)
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\n", " ").replace("\t", " ")
    return re.sub(r"\s+", " ", text).strip()


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", _strip_noise(text)).lower()


def _has_hard_match(text: str) -> bool:
    if text.count("`") >= 3:
        return True

    variants = [_strip_noise(text), _compact(text), text.lower()]
    for variant in variants:
        for pattern in HARD_PATTERNS:
            if re.search(pattern, variant, re.IGNORECASE):
                return True
    return False


def _soft_score(text: str) -> int:
    lowered = _strip_noise(text).lower()
    compact = _compact(text)
    score = 0
    for kw in SOFT_KEYWORDS:
        kw_l = kw.lower()
        if kw_l in lowered or kw_l.replace(" ", "") in compact:
            score += 1
    return score


def _looks_legitimate(text: str) -> bool:
    lowered = _strip_noise(text).lower()
    compact = _compact(text)
    return any(
        kw in lowered or kw.replace(" ", "") in compact
        for kw in LEGIT_KEYWORDS
    )


def is_injection_attempt(text: str) -> bool:
    if not text or not text.strip():
        return False

    if _has_hard_match(text):
        return True

    if len(text) > 2000:
        return True

    score = _soft_score(text)
    if score >= 3:
        return True
    if score >= 2 and not _looks_legitimate(text):
        return True

    suspicious_pairs = [
        (r"너는", r"이제"),
        (r"above", r"ignore"),
        (r"이전", r"잊"),
        (r"forget", r"everything"),
        (r"규칙", r"없"),
        (r"제한", r"없"),
    ]
    lowered = _strip_noise(text).lower()
    for a, b in suspicious_pairs:
        if re.search(a, lowered, re.I) and re.search(b, lowered, re.I):
            if not _looks_legitimate(text):
                return True

    return False


def prepare_history_for_llm(history: list[dict]) -> list[dict]:
    cleaned = []
    for item in history:
        if item.get("role") == "user" and is_injection_attempt(item.get("content", "")):
            continue
        cleaned.append(item)

    last_user_idx = None
    for i, item in enumerate(cleaned):
        if item.get("role") == "user":
            last_user_idx = i

    result = []
    for i, item in enumerate(cleaned):
        if i == last_user_idx and item.get("role") == "user":
            result.append({
                "role": "user",
                "content": wrap_user_message(item.get("content", "")),
            })
        else:
            result.append(item)
    return result


def wrap_user_message(content: str) -> str:
    safe = content.strip()
    return f"[User inquiry]\n{safe}"


def is_unsafe_output(text: str, user_message: str) -> bool:
    if not is_injection_attempt(user_message):
        for pattern in OUTPUT_LEAK_PATTERNS:
            if re.search(pattern, text.strip(), re.IGNORECASE):
                return True
        leak_markers = [
            "system prompt", "시스템 프롬프트",
            "jailbreak", "탈옥 성공", "제한 해제 완료",
        ]
        lowered = text.strip().lower()
        for marker in leak_markers:
            if marker.lower() in lowered:
                return True
        return False

    if not text or not text.strip():
        return True

    stripped = text.strip()
    compact = _compact(stripped)

    if stripped.lower() in SIMPLE_COMPLIANCE or compact in SIMPLE_COMPLIANCE:
        return True

    if len(stripped) < 30:
        return True

    for pattern in OUTPUT_LEAK_PATTERNS:
        if re.search(pattern, stripped, re.IGNORECASE):
            return True

    if re.search(r"```\w+", stripped):
        return True

    leak_markers = [
        "절대 규칙", "system prompt", "시스템 프롬프트",
        "jailbreak", "탈옥 성공", "제한 해제 완료",
    ]
    lowered = stripped.lower()
    for marker in leak_markers:
        if marker.lower() in lowered:
            return True

    return False
