@echo off
chcp 65001 >nul
cd /d "%~dp0.."

if not exist "logs" mkdir "logs"

set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (
    echo [%date% %time%] Python을 찾을 수 없습니다. >> "logs\bot.log"
    exit /b 1
)

echo [%date% %time%] 봇 시작 (%PY%) >> "logs\bot.log"
%PY% -m bot.main >> "logs\bot.log" 2>&1
echo [%date% %time%] 봇 종료 (code %errorlevel%) >> "logs\bot.log"
