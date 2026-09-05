# AI Ticket Bot

Discord support ticket bot with local Ollama replies. Opens private tickets, answers first, and can ping staff when needed.

## Features

- Ticket panel for 1:1 inquiry channels
- Auto thread replies in public support channels
- Per-server custom prompt
- Terms agreement before AI chat
- Basic prompt-injection guard
- Optional abuse log channel

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com/)
- Discord bot token (enable Message Content Intent and Server Members Intent)

## Setup

```bash
git clone https://github.com/TUBERO1/AI-Ticket-Bot.git
cd AI-Ticket-Bot
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill `.env`:

```env
DISCORD_TOKEN=
DEVELOPER_IDS=
ABUSE_LOG_CHANNEL_ID=
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=exaone3.5:7.8b
OLLAMA_MAX_TOKENS=2048
OLLAMA_TEMPERATURE=0.7
```

`DEVELOPER_IDS` is a comma-separated list of Discord user IDs. Only those users can run slash commands.

```bash
ollama pull exaone3.5:7.8b
ollama serve
```

## Run

```bash
python -m bot.main
```

Or use `scripts\start_bot.bat`.

Autostart on Windows login: `scripts\install_autostart.ps1`

## First-time config

1. Invite the bot
2. `/server-setup ticket-category`
3. `/server-setup staff-role`
4. `/server-setup add-support` (public inquiry channel)
5. `/ticket-panel`
6. Optional: `/server-setup set-prompt`
7. Optional: `/bot-setup` for Ollama settings

Full list: `/commands`

## Layout

```
bot/        bot code
scripts/    run / autostart helpers
data/       sqlite db (gitignored)
logs/       logs (gitignored)
```

## License

MIT
