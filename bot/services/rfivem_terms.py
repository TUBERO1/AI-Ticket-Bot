import re

from bot.services.guard import _compact, _strip_noise

DEF_QUERY = re.compile(
    r"(뭐|무엇|뭔|뭔가|뭐야|뭐죠|뭔지|무슨|설명|정의|뜻|의미|알려|가르쳐|말해|해줘|궁금)",
    re.I,
)

TERM_ALIASES = [
    (r"배드\s*알피", "bad_rp"),
    (r"bad\s*rp", "bad_rp"),
    (r"badrp", "bad_rp"),
    (r"논\s*알피", "non_rp"),
    (r"논알피", "non_rp"),
    (r"non\s*rp", "non_rp"),
    (r"nonrp", "non_rp"),
    (r"파워\s*게이밍", "powergaming"),
    (r"power\s*gaming", "powergaming"),
    (r"powergaming", "powergaming"),
    (r"메타\s*게이밍", "metagaming"),
    (r"metagaming", "metagaming"),
    (r"메타게이밍", "metagaming"),
    (r"이중\s*알피", "dual_rp"),
    (r"이중알피", "dual_rp"),
    (r"이중\s*rp", "dual_rp"),
    (r"rdm", "rdm"),
    (r"vdm", "vdm"),
    (r"ooc", "ooc"),
    (r"ic", "ic"),
    (r"필드\s*알피", "field_rp"),
    (r"필드\s*rp", "field_rp"),
    (r"스토리\s*알피", "story_rp"),
    (r"스토리\s*rp", "story_rp"),
    (r"역할\s*극", "rp"),
    (r"role\s*play", "rp"),
    (r"roleplay", "rp"),
    (r"알피", "rp"),
    (r"\brp\b", "rp"),
]

ONGOING_RP = ("도주", "추격", "수배", "체포", "강도", "납치", "전투", "추격전", "검거", "조직전", "구금")


def short_reply(verdict: str, reason: str, result: str, note: str = "") -> str:
    lines = [
        f"**판정:** {verdict}",
        f"**이유:** {reason}",
        f"**결과:** {result}",
    ]
    if note:
        lines.append(f"**참고:** {note}")
    return "\n".join(lines)


TERM_REPLIES = {
    "bad_rp": short_reply(
        "Bad RP (용어)",
        "RP는 하지만 현실성·개연성이 부족해 몰입을 깨는 행위(제16·20·22조).",
        "상황에 따라 Non-RP와 함께 1~5급 또는 운영 제재(제79조).",
    ),
    "non_rp": short_reply(
        "Non-RP (용어)",
        "현실성·게임 질서를 무시한 비정상 RP(제19조). RDM·메타·이중 RP 등 포함.",
        "1~5급 또는 운영 제재(제79조).",
    ),
    "rp": short_reply(
        "RP / 알피 (용어)",
        "Roleplay(역할극). 필드 RP(일반)와 스토리 RP(이벤트 카드)로 나뉨(제5·70조).",
        "용어 설명 — 처벌 없음.",
        "OOC=현실 대화, RP=캐릭터 행동.",
    ),
    "powergaming": short_reply(
        "파워게이밍 (용어)",
        "상대 대응 없이 결과를 일방 확정하는 행위(제18조).",
        "1~5급 또는 운영 제재.",
    ),
    "metagaming": short_reply(
        "메타게이밍 (용어)",
        "디스코드·방송·스크린샷 등 밖 정보를 RP에 쓰는 행위(제17조).",
        "Non-RP·1~5급 또는 운영 제재.",
    ),
    "dual_rp": short_reply(
        "이중 RP (용어)",
        "주요 RP 미종료 중 다른 주요 RP 시작·개입(제24~25조).",
        "Non-RP·1~5급, 사건 무효·재진행 가능(제27조).",
        "예외: 동차 참여·무관 지역 생활 RP·운영진 승인(제26조).",
    ),
    "rdm": short_reply(
        "RDM (용어)",
        "동기·RP 없이 공격·살해(제21조).",
        "Non-RP·1~5급 또는 운영 제재.",
    ),
    "vdm": short_reply(
        "VDM (용어)",
        "차량으로 고의 피해(제21조). 교통사고 RP는 고의 없으면 제외.",
        "1~5급 또는 운영 제재.",
    ),
    "ooc": short_reply(
        "OOC (용어)",
        "캐릭터 밖 현실 대화. 전체 채널은 비RP·문의용.",
        "카테고리 오용 시 Non-RP 제재 가능.",
    ),
    "ic": short_reply(
        "IC (용어)",
        "캐릭터 관점 대화·행동. 인스타 채널은 게임 내 SNS RP.",
        "용어 설명 — 처벌 없음.",
    ),
    "field_rp": short_reply(
        "필드 RP (용어)",
        "이벤트 카드 없이 자연 발생하는 일반 RP(제5조).",
        "용어 설명 — 처벌 없음.",
    ),
    "story_rp": short_reply(
        "스토리 RP (용어)",
        "이벤트 카드·운영진 승인 공식 사건 RP(제70~71조).",
        "카드 없이 대규모 진행 시 Non-RP(제75조).",
    ),
}


def normalize_rfivem_text(text: str) -> str:
    t = _strip_noise(text)
    replacements = [
        (r"배드\s*알피", "Bad RP"),
        (r"bad\s*rp", "Bad RP"),
        (r"badrp", "Bad RP"),
        (r"논\s*알피", "Non-RP"),
        (r"논알피", "Non-RP"),
        (r"non\s*rp", "Non-RP"),
        (r"nonrp", "Non-RP"),
        (r"이중\s*알피", "이중 RP"),
        (r"이중알피", "이중 RP"),
        (r"이중\s*rp", "이중 RP"),
        (r"필드\s*알피", "필드 RP"),
        (r"필드\s*rp", "필드 RP"),
        (r"스토리\s*알피", "스토리 RP"),
        (r"스토리\s*rp", "스토리 RP"),
        (r"파워\s*게이밍", "파워게이밍"),
        (r"power\s*gaming", "파워게이밍"),
        (r"메타\s*게이밍", "메타게이밍"),
        (r"역할\s*극", "RP"),
        (r"role\s*play", "RP"),
        (r"roleplay", "RP"),
        (r"알피", "RP"),
        (r"\brp\b", "RP"),
    ]
    for pattern, repl in replacements:
        t = re.sub(pattern, repl, t, flags=re.I)
    return t


def _has_words(text: str, words: tuple[str, ...]) -> bool:
    lowered = _strip_noise(text).lower()
    compact = _compact(text)
    for word in words:
        w = word.lower()
        if w in lowered or w in compact:
            return True
    return False


def _detect_term(text: str) -> str | None:
    compact = _compact(text)
    lowered = _strip_noise(text).lower()
    for pattern, term_id in TERM_ALIASES:
        if re.search(pattern, lowered, re.I) or re.search(pattern.replace(r"\s*", ""), compact, re.I):
            return term_id
    return None


def try_scenario_reply(text: str) -> str | None:
    if not text or not text.strip():
        return None

    n = normalize_rfivem_text(text)

    if _has_words(n, ONGOING_RP) and _has_words(n, ("스토리",)):
        return short_reply(
            "이중 RP · Non-RP",
            "도주·추격·수배 RP가 끝나기 전에 스토리 RP를 같이 하면 주요 RP 2개 병행(제24~25조).",
            "운영 제재 또는 1~5급. 사건 무효·재진행 가능(제27조).",
            "한쪽 끝난 뒤 시작하거나 운영진 승인·이벤트 카드 허용 시만 병행(제26조).",
        )

    if _has_words(n, ("체포", "구금", "수색")) and _has_words(n, ("강도", "납치", "다른", "별도")):
        return short_reply(
            "이중 RP · Non-RP",
            "체포·구금 RP 중 다른 강도·납치 RP 시작(제25조).",
            "운영 제재·사건 무효·재진행 가능(제27조).",
            "즉시 중단·이탈 후 운영진 문의.",
        )

    if _has_words(n, ("추격", "추격전")) and _has_words(n, ("제3자", "난입", "끼어", "개입", "다른 전투")):
        return short_reply(
            "이중 RP · Non-RP",
            "추격전 중 제3자가 별도 전투를 열어 결과를 바꿈(제25조).",
            "운영 제재·사건 무효·재진행 가능(제27조).",
        )

    if _has_words(n, ("이미",)) and _has_words(n, ("제압", "죽였", "죽임", "훔쳤", "납치했")):
        return short_reply(
            "파워게이밍",
            "상대 대응 없이 결과를 일방 확정(제18조).",
            "1~5급 또는 운영 제재.",
            "상대에게 반응·선택 시간을 줘야 함.",
        )

    if _has_words(n, ("디스코드", "방송", "스크린샷", "dm", "디엠")) and _has_words(n, ("위치", "공유", "알려", "좌표")):
        return short_reply(
            "메타게이밍 · Non-RP",
            "인게임 밖 정보를 RP에 사용(제17조).",
            "1~5급 또는 운영 제재.",
        )

    if _has_words(n, ("사망", "기절")) and _has_words(n, ("다시", "재참여", "또", "같은")):
        return short_reply(
            "Non-RP",
            "사망·기절 후 같은 사건 재참여·보복(제28·29조).",
            "1~5급 또는 운영 제재.",
        )

    if _has_words(n, ("이유", "동기", "대화")) and _has_words(n, ("없이", "갑자기")) and _has_words(n, ("쏴", "총", "살해", "공격")):
        return short_reply(
            "RDM · Non-RP",
            "동기·RP 없이 공격·살해(제21조).",
            "1~5급 또는 운영 제재.",
        )

    if _has_words(n, ("차", "차량")) and _has_words(n, ("박", "들이받", "치")) and _has_words(n, ("고의", "일부러")):
        return short_reply(
            "VDM",
            "차량으로 고의 피해(제21조).",
            "1~5급 또는 운영 제재.",
            "교통사고·렉은 고의 없으면 제외.",
        )

    return None


def try_term_reply(text: str) -> str | None:
    if not text or not text.strip():
        return None

    normalized = normalize_rfivem_text(text)
    compact = _compact(normalized)
    lowered = _strip_noise(normalized).lower()

    if not DEF_QUERY.search(lowered) and len(compact) > 12:
        return None

    term_id = _detect_term(normalized)
    if not term_id:
        return None

    return TERM_REPLIES.get(term_id)


def try_rfivem_quick_reply(text: str) -> str | None:
    return try_scenario_reply(text) or try_term_reply(text)
