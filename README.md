# Lumentia AI Ticket Bot

Discord 문의 티켓·채널 자동응답 봇입니다.  
로컬 Ollama LLM으로 1차 응대하고, 필요하면 관리자를 호출할 수 있습니다.

## 기능

- 티켓 패널로 1:1 문의 채널 생성
- 문의 채널 스레드 자동 생성·응답
- 서버별 모드: `Lumentia`(외주 문의) / `RFIVEM`(법률·RP 판별)
- 서버별 커스텀 프롬프트
- 이용약관 동의 후 AI 상담
- 프롬프트 인젝션·범위 밖 질문 가드
- 악용 시도 로그 채널 전송 (선택)

## 요구 사항

- Python 3.11+
- [Ollama](https://ollama.com/) 실행 중
- Discord 봇 토큰 (Message Content Intent, Server Members Intent 권장)

## 설치

```bash
git clone https://github.com/kore0307/Lumentia-AI-Ticket-Bot.git
cd Lumentia-AI-Ticket-Bot
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

`.env` 예시:

```env
DISCORD_TOKEN=봇토큰
DEVELOPER_IDS=본인디스코드유저ID
ABUSE_LOG_CHANNEL_ID=
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=exaone3.5:7.8b
OLLAMA_MAX_TOKENS=2048
OLLAMA_TEMPERATURE=0.7
```

`DEVELOPER_IDS`는 쉼표로 여러 명 가능합니다.  
슬래시 명령은 여기에 등록된 개발자만 사용할 수 있습니다.

모델 준비:

```bash
ollama pull exaone3.5:7.8b
ollama serve
```

## 실행

```bash
python -m bot.main
```

Windows 스크립트:

```bat
scripts\start_bot.bat
```

로그인 시 자동 실행:

```powershell
scripts\install_autostart.ps1
```

## 기본 설정 흐름

1. 봇을 서버에 초대
2. `/서버설정 모드` — Lumentia 또는 RFIVEM
3. `/서버설정 티켓카테고리` — 티켓이 생길 카테고리
4. `/서버설정 관리자역할` — 관리자 호출 멘션용
5. `/서버설정 문의채널등록` — 공개 문의 채널 (스레드 방식)
6. `/티켓패널` — 티켓 버튼 패널 배포
7. (선택) `/서버설정 프롬프트설정` — 서버 전용 안내문
8. (선택) `/봇설정` — Ollama 모델·주소·토큰·온도

명령 전체 목록은 `/명령어`로 확인할 수 있습니다.

## 프로젝트 구조

```
bot/
  main.py            진입점
  config.py          환경변수
  db.py              SQLite
  cogs/              슬래시 명령·이벤트
  services/          LLM, 가드, 프롬프트
  views/             버튼·모달
scripts/             실행·자동시작
```

데이터는 `data/bot.db`, 로그는 `logs/`에 저장됩니다.  
둘 다 git에 포함되지 않습니다.

## 라이선스

MIT
