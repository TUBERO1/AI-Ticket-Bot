import re

import discord

SAFE_MENTIONS = discord.AllowedMentions.none()

_TAG_CLEANUP = [
    (re.compile(r"</?user>", re.I), ""),
    (re.compile(r"\[고객\s*문의\]", re.I), ""),
]

_MENTION_PATTERNS = [
    re.compile(r"@\s*everyone", re.I),
    re.compile(r"@\s*here", re.I),
    re.compile(r"<!everyone>", re.I),
    re.compile(r"<!here>", re.I),
    re.compile(r"<@&\d+>"),
    re.compile(r"@\u200b*everyone", re.I),
    re.compile(r"@\u200b*here", re.I),
    re.compile(r"everyone\s*멘션", re.I),
    re.compile(r"here\s*멘션", re.I),
    re.compile(r"모두\s*멘션", re.I),
    re.compile(r"전체\s*멘션", re.I),
]


def sanitize_reply(text: str) -> str:
    if not text:
        return text

    cleaned = text
    for pattern, repl in _TAG_CLEANUP:
        cleaned = pattern.sub(repl, cleaned)

    for pattern in _MENTION_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def split_reply_for_send(text: str) -> tuple[str | None, str | None]:
    if not text:
        return None, None
    return text.rstrip(), None
