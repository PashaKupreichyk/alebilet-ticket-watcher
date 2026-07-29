@echo off
cd /d "%~dp0"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing dependencies (first run only, may take a few minutes)...
pip install -r requirements.txt --quiet
playwright install chromium

echo.
echo Starting ticket watcher. Leave this window open.
echo Press Ctrl+C to stop.
echo.

set TELEGRAM_BOT_TOKEN=8913768692:AAEgWMTdmWY3o9bQp33KJRWjnW0s99Wrts0
set TELEGRAM_CHAT_ID=557515518
set POLL_SECONDS=15

python run_local.py

pause
