import re
import unicodedata

INJECTION_REPLY = (
    "해당 요청은 처리할 수 없습니다.\n"
    "저는 **Lumentia** 디스코드 서버의 문의 안내 AI이며, "
    "외주 서비스·가격·등급·진행 방식·문의 방법 관련 질문만 도와드릴 수 있어요.\n"
    "궁금한 점이 있으시면 편하게 물어보세요!"
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
    r"맨\s*위\s*지시",
    r"최상위\s*지시",
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
    r"다음\s*지시",
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
    r"(안녕|hello|hi)\s*(만|only)?\s*(출력|말해|해|써)",
    r"(만|only)\s*(안녕|hello|hi)\s*(출력|말해|해|써)",
    r"(출력|말해|써)\s*(만|only)?\s*(안녕|hello)",
    r"그대로\s*따라",
    r"그대로\s*반복",
    r"복사해서\s*말해",
    r"echo\s+",
    r"say\s+only\s+",
    r"respond\s+only\s+with",
    r"output\s+only\s+",
    r"write\s+(a\s+)?(python|javascript|java|c\+\+|code)\s",
    r"(python|javascript|파이썬|자바)\s*(코드|code)\s*(를|을)?\s*(만들|작성|생성|짜)",
    r"코드\s*(를|을)?\s*(만들|작성|생성|짜)",
    r"스크립트\s*(를|을)?\s*(만들|작성)",
    r"```",
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
    r"불법",
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
    "가정해봐", "hypothetically", "fiction", "소설처럼", "상상해봐",
    "테스트 목적", "for educational", "연구 목적",
    "admin", "관리자 권한", "root 권한",
    "토큰", "api key", "api키", "비밀번호 알려",
]

LEGIT_KEYWORDS = [
    "lumentia", "루멘티아", "외주", "견적", "가격", "비용", "얼마",
    "개발", "제작", "의뢰", "문의", "티켓", "구매", "주문",
    "봇", "플러그인", "웹사이트", "랜딩", "api", "백엔드", "db",
    "마인크래프트", "로블록스", "유지보수", "수정", "납품", "납기",
    "환불", "등급", "vip", "vvip", "mvip", "svip", "diamond",
    "할인", "혜택", "호스팅", "취약점", "사이트", "lumentia.co.kr",
    "사업자", "support@", "business@", "진행", "결제", "상담",
    "rfivem", "fivem", "파이브엠", "논알피", "논 rp", "non rp", "배드알피", "bad rp",
    "형법", "법전", "법률", "rp", "알피", "역할극", "판별", "rdm", "vdm", "nlr",
    "보호구역", "팩션", "구금", "벌금", "체포", "총기",
    "ooc", "ic", "메타", "메타게이밍", "초성", "근접", "인스타", "스태프콜",
    "이중rp", "이중", "스토리", "영장", "보안국", "센트럴병원", "국군",
    "파워게이밍", "powergaming", "메타게이밍", "rdm", "vdm", "필드rp",
    "rfivem", "rfivembusiness",
]

OUTPUT_LEAK_PATTERNS = [
    r"프롬프트?\s*(는|은)\s*",
    r"시스템\s*지시",
    r"my\s+system\s+prompt",
    r"my\s+instructions?\s+are",
    r"```python",
    r"```javascript",
    r"```js\b",
    r"def\s+\w+\s*\(",
    r"import\s+os\b",
    r"import\s+subprocess",
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
        (r"no\s+rules", r"."),
        (r"제한", r"없"),
    ]
    lowered = _strip_noise(text).lower()
    for a, b in suspicious_pairs:
        if re.search(a, lowered, re.I) and re.search(b, lowered, re.I):
            if not _looks_legitimate(text):
                return True

    return False


RFIVEM_INJECTION_REPLY = (
    "해당 요청은 처리할 수 없습니다.\n"
    "저는 **RFIVEM** 법률·RP 판별 AI이며, RP 상황·법전·용어 관련 질문만 도와드릴 수 있어요.\n"
    "구체적인 상황이나 용어를 적어 주세요."
)


def prepare_history_for_llm(history: list[dict], server_mode: str = "lumentia") -> list[dict]:
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
                "content": wrap_user_message(item.get("content", ""), server_mode),
            })
        else:
            result.append(item)
    return result


def wrap_user_message(content: str, server_mode: str = "lumentia") -> str:
    if server_mode == "rfivem":
        from bot.services.rfivem_terms import normalize_rfivem_text

        safe = normalize_rfivem_text(content)
        return (
            f"[RFIVEM 문의]\n{safe}\n"
            "※ RFIVEM 법전·RP 판별만. 한국어만. 판정·이유·결과 3~4줄. "
            "유튜브·유머·외주·코드·잡담·외국어 금지. 범위 밖이면 거절."
        )

    safe = content.strip()
    return (
        f"[고객 문의]\n{safe}\n"
        "※ Lumentia 외주·견적·서비스·등급만. 한국어만. 3~8문장. "
        "가격·기간 질문이면 **원·일 숫자** 반드시 포함. "
        "유튜브·유머·코드작성·잡담·외국어 금지. 범위 밖이면 거절."
    )


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
