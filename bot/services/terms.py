TERMS_VERSION = "2026-09-05"

TERMS_TITLE = "AI Ticket Bot Terms"

TERMS_SECTIONS = [
    (
        "Overview",
        "**Last updated:** September 5, 2026\n\n"
        "These terms cover use of the AI Ticket Bot.\n"
        "Using the service means you accept them."
    ),
    (
        "Use",
        "• Follow Discord's Terms of Service and your server rules\n"
        "• AI answers are for reference only and may be wrong\n"
        "• The service may stop for maintenance or outages"
    ),
    (
        "Prohibited",
        "1. Prompt injection or system abuse\n"
        "2. Macros / spam floods\n"
        "3. Hacking, malware, or illegal requests\n"
        "4. Harassment, threats, or hate speech\n"
        "5. Collecting or leaking personal data\n"
        "6. Disrupting bot or server operations"
    ),
    (
        "Logs & limits",
        "We may store inquiry text, Discord IDs, channel/server IDs, and abuse logs.\n"
        "Violations can lead to access being blocked."
    ),
    (
        "Disclaimer",
        "To the extent allowed by law, we are not liable for damages from relying on AI answers, "
        "Discord/network failures, or force majeure."
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
            embed.set_footer(text=f"Version {TERMS_VERSION}")
        embeds.append(embed)
    return embeds
