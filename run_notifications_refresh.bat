@echo off
REM ── Daily notification refresh (document expiries + labour camp renewals) ─────
REM Called by Windows Task Scheduler once a day. Regenerates document-expiry
REM alerts (visa/EID/labour card/MOL/vehicle mulkiya/management) and the weekly
REM labour-camp-contract renewal reminders so they show up in /notifications/
REM without waiting for HR to open that page. Writes a self-rotating log to
REM logs\notifications.log (max 2 files), so no redirection is needed here.
REM Only catastrophic startup errors go to logs\notifications.boot.log.
setlocal

set PROJECT_DIR=D:\dataanalyst\Data Analysis\HR-MODULE\hr_module
set PYTHON=D:\dataanalyst\Data Analysis\HR-MODULE\venv\Scripts\python.exe

cd /d "%PROJECT_DIR%"
"%PYTHON%" manage.py generate_expiry_notifications 2>> "%PROJECT_DIR%\logs\notifications.boot.log"

endlocal
