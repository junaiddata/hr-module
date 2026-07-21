@echo off
REM ── Daily WhatsApp labour-card renewal reminders ──────────────────────────────
REM Called by Windows Task Scheduler once a day. Sends a WhatsApp prompt to any
REM employee whose labour card is within 60 days of expiry (each employee is only
REM ever prompted once per expiry date — see LabourCardRenewalPrompt dedup in the
REM command). The app writes a self-rotating log to logs\labour_card_renewal.log
REM (max 2 files), so no redirection is needed here. Only catastrophic startup
REM errors go to logs\labour_card_renewal.boot.log.
setlocal

set PROJECT_DIR=D:\dataanalyst\Data Analysis\HR-MODULE\hr_module
set PYTHON=D:\dataanalyst\Data Analysis\HR-MODULE\venv\Scripts\python.exe

cd /d "%PROJECT_DIR%"
"%PYTHON%" manage.py send_labour_card_renewal_reminders 2>> "%PROJECT_DIR%\logs\labour_card_renewal.boot.log"

endlocal
