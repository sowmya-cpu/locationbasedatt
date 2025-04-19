@echo off
REM — base directory where this .bat lives 
set BASEDIR=%~dp0

REM — try activating .venv first, else venv
if exist "%BASEDIR%.venv\Scripts\activate.bat" (
    call "%BASEDIR%.venv\Scripts\activate.bat"
) else if exist "%BASEDIR%venv\Scripts\activate.bat" (
    call "%BASEDIR%venv\Scripts\activate.bat"
) else (
    echo ERROR: Couldn’t find activate.bat in .venv or venv folder.
    pause
    exit /b 1
)

REM — run your Django command
python "%BASEDIR%manage.py" mark_absentees

REM — log exit code
echo Exit code: %ERRORLEVEL%
pause
