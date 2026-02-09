@echo off
setlocal enabledelayedexpansion

echo.
echo ==========================================
echo   🚀 PUSHING CODE TO GITHUB (FORCE MODE)
echo ==========================================
echo.

REM ---- Check Git ----
git --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ❌ Git not found
    pause
    exit /b
)

REM ---- Init repo if missing ----
IF NOT EXIST ".git" (
    git init
)

REM ---- Add remote if missing ----
git remote get-url origin >nul 2>&1
IF ERRORLEVEL 1 (
    git remote add origin https://github.com/vsrepalle/youtube_videos.git
)

REM ---- Ensure main branch ----
git branch -M main

REM ---- Create .gitignore if missing ----
IF NOT EXIST ".gitignore" (
(
echo __pycache__/
echo *.pyc
echo *.env
echo .env
echo oauth_token.json
echo token.json
echo credentials.json
echo *.mp4
echo *.avi
echo *.mov
echo daily_outputs/
echo output/
echo dist/
echo build/
echo .idea/
echo .vscode/
) > .gitignore
)

REM ---- Add everything ----
git add .

REM ---- Commit ----
git commit -m "Auto update %DATE% %TIME%" >nul 2>&1

REM ---- FORCE PUSH ----
echo 🔥 Force pushing to GitHub...
git push -u origin main --force

echo.
echo ==========================================
echo   ✅ PUSH COMPLETE (REMOTE REPLACED)
echo ==========================================
echo.
pause
