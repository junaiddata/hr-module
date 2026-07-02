@echo off
REM ── Daily WhatsApp birthday wishes ────────────────────────────────────────────
REM Called by Windows Task Scheduler once a day. The app writes a self-rotating
REM log to logs\birthday_wishes.log (max 2 files), so no redirection is needed
REM here. Only catastrophic startup errors go to logs\birthday_wishes.boot.log.
setlocal

set PROJECT_DIR=D:\dataanalyst\Data Analysis\HR-MODULE\hr_module
set PYTHON=D:\dataanalyst\Data Analysis\HR-MODULE\venv\Scripts\python.exe

cd /d "%PROJECT_DIR%"
"%PYTHON%" manage.py send_birthday_wishes 2>> "%PROJECT_DIR%\logs\birthday_wishes.boot.log"

endlocal
