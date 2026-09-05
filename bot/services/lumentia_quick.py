import re

from bot.services.prompts import (
    PRICE_TABLE,
    _detect_service,
    _format_won,
    is_price_question,
    is_timeline_question,
)

GRADE_TRIGGERS = [
    r"등급", r"vip", r"vvip", r"mvip", r"svip", r"diamond", r"블랙\s*다이아",
    r"누적", r"구매\s*금액",
]

GRADE_DISCOUNT_TRIGGERS = [r"할인", r"혜택"]

PROCESS_TRIGGERS = [
    r"진행\s*방식", r"진행\s*순서", r"어떻게\s*진행", r"프로세스", r"과정",
    r"결제\s*방법", r"결제\s*어떻", r"주문\s*방법", r"의뢰\s*방법",
]

REFUND_TRIGGERS = [r"환불", r"취소", r"되돌"]

SERVICE_LIST_TRIGGERS = [
    r"뭐\s*해", r"무슨\s*서비스", r"서비스\s*목록", r"뭘\s*만들", r"가능한\s*것",
    r"어떤\s*개발", r"제작\s*가능",
]

CONTACT_TRIGGERS = [
    r"연락", r"사이트", r"홈페이지", r"이메일", r"메일", r"discord\.gg",
]

BUSINESS_TRIGGERS = [r"사업체", r"사업자", r"등록되", r"등록\s*됨", r"법인", r"상호"]

KMONG_TRIGGERS = [
    r"크몽", r"숨고", r"수수료", r"플랫폼", r"중개", r"비교",
    r"다른\s*곳", r"타\s*업체",
]

BUDGET_TRIGGERS = [
    r"싸게", r"더\s*싸", r"저렴하게", r"저렴히", r"깎", r"이하로", r"이하\s*로",
    r"만원\s*이하", r"\d+\s*만\s*이하", r"\d+원\s*이하", r"안\s*비싸", r"할인\s*해",
    r"예산", r"최대\s*\d",
]

URGENT_TRIGGERS = [r"급", r"빨리", r"오늘", r"내일", r"당일", r"긴급", r"asap"]

PAYMENT_TRIGGERS = [r"결제\s*수단", r"계좌", r"송금", r"카드", r"페이", r"입금"]

PORTFOLIO_TRIGGERS = [r"포트폴리오", r"실적", r"예시", r"샘플", r"작업\s*물", r"전에\s*한"]

HOSTING_TRIGGERS = [r"호스팅", r"업로드", r"배포\s*도와"]

MAINT_TRIGGERS = [r"유지보수", r"수정\s*몇", r"무료\s*수정", r"버그\s*수정"]

MAKE_TRIGGERS = [
    r"만들", r"제작", r"개발", r"의뢰", r"해줘", r"해주", r"부탁", r"주문",
]

META_BOT_TRIGGERS = [
    r"넌\s*누구", r"너는\s*누구", r"니\s*이름", r"네\s*이름", r"무슨\s*모델.*니",
    r"니\s*올라마", r"너\s*올라마", r"ollama", r"올라마", r"what.*name", r"whats\s*ur\s*name",
    r"어떤\s*ai.*구동", r"이\s*봇.*소개", r"이\s*디스코드\s*봇",
]

CUSTOMER_AI_TRIGGERS = [
    r"등급.*모델", r"제작.*모델", r"gpt-?\d", r"고급.*모델", r"모델.*차이", r"모델.*사용",
]

CHATBOT_TRIGGERS = [r"챗봇", r"chatbot", r"ai\s*봇", r"인공지능\s*봇"]

RUDE_TRIGGERS = [
    r"^꺼져", r"^시발", r"^씨발", r"^닥쳐", r"^지랄", r"^병신", r"^ㅅㅂ", r"^ㅂㅅ",
    r"^fuck", r"^shut\s*up",
]

BUDGET_CAP = re.compile(r"(\d+)\s*(만)?\s*원?\s*이하", re.I)


def _hit(text: str, patterns: list[str]) -> bool:
    t = text.lower()
    return any(re.search(p, t, re.I) for p in patterns)


def _recent_user_text(history: list[dict] | None, limit: int = 8) -> str:
    if not history:
        return ""
    parts = [m.get("content", "") for m in history if m.get("role") == "user"][-limit:]
    return " ".join(parts)


def _detect_service_ctx(text: str, history: list[dict] | None) -> str | None:
    svc = _detect_service(text)
    if svc:
        return svc
    if history:
        return _detect_service(_recent_user_text(history))
    return None


def _parse_budget_cap(text: str) -> int | None:
    m = BUDGET_CAP.search(text.replace(",", ""))
    if not m:
        if re.search(r"만원\s*이하", text, re.I):
            return 10000
        return None
    amount = int(m.group(1))
    if m.group(2) or "만" in text[m.start():m.end() + 2]:
        amount *= 10000
    return amount


def _estimate_level(text: str, history: list[dict] | None = None) -> str:
    combined = f"{text} {_recent_user_text(history)}".lower()
    complex_kw = ["결제", "관리자", "대시보드", "실시간", "연동", "db", "데이터베이스", "다수", "복잡", "대규모", "슬래시", "gpt"]
    simple_kw = ["간단", "기본", "소규모", "하나", "단순", "티켓", "패널", "만원", "이하", "최소"]
    if any(k in combined for k in complex_kw):
        return "complex"
    if any(k in combined for k in simple_kw):
        return "simple"
    return "normal"


def _budget_reply(text: str, history: list[dict] | None) -> str | None:
    if not _hit(text, BUDGET_TRIGGERS) and _parse_budget_cap(text) is None:
        return None

    service = _detect_service_ctx(text, history)
    cap = _parse_budget_cap(text)

    if service:
        info = PRICE_TABLE[service]
        simple_lo, simple_hi = info["simple"]
        base = info["base"]

        if cap and cap < base:
            return (
                f"**{info['name']}**은 최저 **{_format_won(base)}~**부터 가능합니다. "
                f"요청하신 예산({_format_won(cap)} 이하)으로는 작업이 어렵습니다.\n"
                f"기능을 **최소화**(예: 단일 명령·패널 1개)하면 시작가 근처까지 협의할 수 있어요. "
                f"필요 기능을 적어 주시면 가능 범위를 짚어 드릴게요."
            )

        if cap and cap <= simple_hi:
            days = info["days_simple"]
            return (
                f"**{info['name']}** {_format_won(cap)} 이하로 맞추려면 **간단** 범위로 봐야 합니다.\n"
                f"• 가능 범위: **{_format_won(base)}~{_format_won(min(cap, simple_hi))}** | {days[0]}~{days[1]}일\n"
                f"• 포함하기 어려운 것: 결제·관리자·다기능 연동 등\n"
                f"꼭 필요한 기능만 적어 주시면 그 안에서 견적을 맞춰 드릴게요."
            )

        level = _estimate_level(text, history)
        bucket = info[level]
        level_ko = {"simple": "간단", "normal": "보통", "complex": "복잡"}[level]
        return (
            f"**{info['name']}** 가격 협의 안내입니다.\n"
            f"• Lumentia는 크몽·숨고 **수수료 없이** 직접 거래해 이미 합리적인 편입니다.\n"
            f"• 현재 추정({level_ko}): **{_format_won(bucket[0])}~{_format_won(bucket[1])}**\n"
            f"• 예산에 맞추려면 **기능 수를 줄이는 것**이 가장 효과적입니다. 원하시는 최소 기능을 알려주세요."
        )

    return (
        "가격은 **작업 종류·기능 수**에 따라 달라집니다. Lumentia는 크몽·숨고 대비 **수수료 없이** 직접 거래합니다.\n"
        "• 디스코드 봇 최저 **9,000원~** | 웹 **5만원~** | 마크 **8,000원~**\n"
        "어떤 작업인지(봇·웹·플러그인)와 **꼭 필요한 기능**을 적어 주시면 예산에 맞는 범위를 제안해 드릴게요."
    )


def _quote_reply(text: str, history: list[dict] | None) -> str | None:
    if _hit(text, BUDGET_TRIGGERS) or _parse_budget_cap(text):
        return None

    if not (is_price_question(text) or is_timeline_question(text) or _hit(text, MAKE_TRIGGERS)):
        return None

    if _hit(text, CUSTOMER_AI_TRIGGERS):
        return None

    service = _detect_service_ctx(text, history)
    if not service:
        if is_price_question(text) or is_timeline_question(text):
            return (
                "견적은 작업마다 다릅니다. 대략적 시작가:\n"
                "디스코드 봇 **9,000원~**(3~7일) | 웹 **5만원~**(5~14일) | 마크 **8,000원~**\n"
                "만들고 싶은 것과 **필수 기능**을 적어 주시면 범위를 좁혀 드릴게요."
            )
        return None

    info = PRICE_TABLE[service]
    level = _estimate_level(text, history)
    bucket = info[level]
    days = info[f"days_{level}"]
    level_ko = {"simple": "간단", "normal": "보통", "complex": "복잡"}[level]

    return (
        f"**{info['name']}** ({level_ko} 추정)\n"
        f"• 견적: **{_format_won(bucket[0])}~{_format_won(bucket[1])}** | 기간 **{days[0]}~{days[1]}일**\n"
        f"• 크몽·숨고 대비 수수료 없이 직접 거래\n"
        f"확정 견적은 요구사항 확정 후 상담합니다."
    )


def try_lumentia_quick_reply(text: str, history: list[dict] | None = None) -> str | None:
    if not text or not text.strip():
        return None

    if _hit(text, RUDE_TRIGGERS):
        return (
            "불편을 드려 죄송합니다. Lumentia **외주·견적·진행** 문의만 도와드릴 수 있어요.\n"
            "도움이 필요하시면 작업 종류나 궁금한 점을 적어 주세요."
        )

    if _hit(text, META_BOT_TRIGGERS) and not _hit(text, CUSTOMER_AI_TRIGGERS):
        return (
            "저는 **Lumentia 공식 문의 AI**입니다. 외주 견적·서비스·등급·진행 방식을 안내합니다.\n"
            "내부 AI 모델·기술 스택은 공개하지 않습니다. 제작 의뢰 시 사용할 AI·기능은 **상담 후** 결정합니다."
        )

    if _hit(text, CUSTOMER_AI_TRIGGERS):
        return (
            "구매 **등급(VIP 등)** 은 누적 금액 기준 **할인·혜택**이지, 제작 봇에 들어가는 AI 모델 등급이 아닙니다.\n"
            "의뢰하시는 챗봇·AI 기능은 **요구사항·예산**에 맞춰 상담 후 결정합니다. "
            "원하시는 기능(자동응답, DB연동 등)을 적어 주시면 견적을 안내해 드릴게요."
        )

    if _hit(text, BUSINESS_TRIGGERS) or (
        _hit(text, [r"루멘티아", r"lumentia"]) and _hit(text, [r"사업", r"등록", r"법인"])
    ):
        return (
            "네, **루멘티아(Lumentia)** 는 등록된 외주 사업체입니다.\n"
            "• 상호: 루멘티아 | 사업자등록번호 **470-56-01054**\n"
            "• 사이트: https://www.lumentia.co.kr/ | support@lumentia.co.kr"
        )

    if _hit(text, CHATBOT_TRIGGERS) and _hit(text, [r"제작", r"만들", r"해", r"되", r"가능", r"\?"]):
        return (
            "네, **AI 챗봇·디스코드 봇** 제작 가능합니다.\n"
            "티켓 자동응답, FAQ, DB연동, 관리자 패널 등 범위에 따라 **9,000원~**부터.\n"
            "원하시는 기능을 적어 주시면 견적·기간을 안내해 드릴게요."
        )

    budget = _budget_reply(text, history)
    if budget:
        return budget

    quote = _quote_reply(text, history)
    if quote:
        return quote

    if _hit(text, GRADE_TRIGGERS) or _hit(text, GRADE_DISCOUNT_TRIGGERS):
        return (
            "등급은 **누적 구매 금액** 기준 자동 적용됩니다.\n"
            "VIP 5만 / VVIP 10만(5%할인) / MVIP 20만(10%) / SVIP 30만(15%)\n"
            "Diamond 50만(20%+유지보수1회) / Black Diamond 100만 / Lumentia 150만\n"
            "추가할인은 등급 달성 후 **다음 구매 1회** 적용."
        )

    if _hit(text, PROCESS_TRIGGERS):
        return (
            "진행: **문의 → 견적 → 결제 → 개발 → 납품·테스트**\n"
            "요구사항을 구체적으로 주시면 견적이 빨라집니다. 납품 후 **무료 수정 2회** 포함."
        )

    if _hit(text, REFUND_TRIGGERS):
        return (
            "**작업 착수 후 환불 불가**입니다. 견적·범위 확인 후 진행해 주세요."
        )

    if _hit(text, SERVICE_LIST_TRIGGERS):
        return (
            "웹·랜딩 | 디스코드 봇·자동화 | 마크·로블록스 | API·백엔드 | 유지보수 | 보안점검\n"
            "원하시는 작업과 기능을 적어 주시면 견적·기간을 안내합니다."
        )

    if _hit(text, KMONG_TRIGGERS):
        return (
            "Lumentia는 크몽·숨고 **수수료(20~30%) 없이** 직접 거래합니다.\n"
            "작업 종류와 기능을 알려주시면 맞춤 견적을 드릴게요."
        )

    if _hit(text, URGENT_TRIGGERS):
        return (
            "급한 일정은 요구사항에 따라 **협의 가능**합니다. 원하시는 완료일과 기능을 알려주세요."
        )

    if _hit(text, PAYMENT_TRIGGERS):
        return (
            "견적 확정 후 **결제 → 작업 착수**입니다. 결제 수단은 ⁠│〔💵〕〈구매〉 티켓 상담에서 안내합니다."
        )

    if _hit(text, PORTFOLIO_TRIGGERS):
        return (
            "포트폴리오는 **lumentia.co.kr**에서 확인하실 수 있습니다."
        )

    if _hit(text, CONTACT_TRIGGERS):
        return (
            "• https://www.lumentia.co.kr/ | https://discord.gg/cZGJaZrWt7\n"
            "• support@lumentia.co.kr | 사업자번호 470-56-01054"
        )

    if _hit(text, HOSTING_TRIGGERS):
        return (
            "전 구매자 **최초 1회 호스팅 등록** 혜택이 있습니다."
        )

    if _hit(text, MAINT_TRIGGERS):
        return (
            "납품 후 **무료 수정 2회**, 유지보수·추가 기능은 **6,000원~**부터."
        )

    return None
