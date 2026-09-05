# AI Ticket

디스코드 문의 티켓 봇. Ollama로 1차 답하고, 안 되면 관리자 호출.

## 뭘 함

- 티켓 패널 → 1:1 채널
- 문의 채널에 쓰면 스레드 만들고 자동 답변
- 서버마다 프롬프트 따로 넣을 수 있음
- 약관 동의 후에만 AI 상담
- 이상한 프롬프트 공격은 막음

## 필요

- Python 3.11+
- Ollama
- Discord 봇 토큰 (Message Content, Server Members Intent)

## 설치

```bash
git clone https://github.com/kore0307/AI-Ticket.git
cd AI-Ticket
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

`.env` 채우기:

```env
DISCORD_TOKEN=
DEVELOPER_IDS=
ABUSE_LOG_CHANNEL_ID=
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=exaone3.5:7.8b
OLLAMA_MAX_TOKENS=2048
OLLAMA_TEMPERATURE=0.7
```

`DEVELOPER_IDS`는 디스코드 유저 ID. 여러 명이면 쉼표로 이어서.

```bash
ollama pull exaone3.5:7.8b
ollama serve
```

## 실행

```bash
python -m bot.main
```

또는 `scripts\start_bot.bat`

자동 실행은 `scripts\install_autostart.ps1`

## 처음에 할 일

1. 봇 초대
2. `/서버설정 티켓카테고리`
3. `/서버설정 관리자역할`
4. `/서버설정 문의채널등록` (공개 문의용)
5. `/티켓패널`
6. 필요하면 `/서버설정 프롬프트설정`
7. LLM 쪽은 `/봇설정`

전체 목록은 `/명령어`

## 구조

```
bot/        본체
scripts/    실행 스크립트
data/       DB (gitignore)
logs/       로그 (gitignore)
```

## 라이선스

MIT
