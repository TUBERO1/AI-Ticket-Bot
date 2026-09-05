TERMS_VERSION = "2026-09-05"

TERMS_TITLE = "AI 문의봇 이용약관"

TERMS_SECTIONS = [
    (
        "개요",
        "**최종 수정일:** 2026년 9월 5일\n\n"
        "이 약관은 AI 문의봇 이용 조건을 정합니다.\n"
        "서비스를 쓰면 약관에 동의한 것으로 봅니다."
    ),
    (
        "이용",
        "• Discord 이용약관과 서버 규칙을 지킨다\n"
        "• AI 답변은 참고용이며 항상 맞다고 보장하지 않는다\n"
        "• 운영 중 점검이나 장애로 서비스가 멈출 수 있다"
    ),
    (
        "금지",
        "1. 프롬프트 조작·인젝션\n"
        "2. 매크로·스팸 반복\n"
        "3. 해킹·악성코드·불법 요청\n"
        "4. 욕설·협박·혐오 표현\n"
        "5. 타인 개인정보 수집·유출\n"
        "6. 봇·서버 운영 방해"
    ),
    (
        "기록 · 제한",
        "문의 내용, Discord ID, 채널·서버 ID, 악용 로그를 남길 수 있다.\n"
        "약관 위반 시 이용을 막을 수 있다."
    ),
    (
        "면책",
        "AI 답변을 믿고 생긴 손해, Discord·네트워크 장애, 불가항력에 대해 "
        "법령이 허용하는 범위에서 책임을 지지 않는다."
    ),
]


def build_terms_embeds() -> list:
    import discord

    embeds = []
    for i, (title, body) in enumerate(TERMS_SECTIONS, 1):
        embed = discord.Embed(
            title=f"{TERMS_TITLE} ({i}/{len(TERMS_SECTIONS)}) — {title}",
            description=body,
            color=discord.Color.blurple(),
        )
        if i == len(TERMS_SECTIONS):
            embed.set_footer(text=f"버전 {TERMS_VERSION}")
        embeds.append(embed)
    return embeds
