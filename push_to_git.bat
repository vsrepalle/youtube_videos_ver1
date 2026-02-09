@echo off
echo ============================================
echo   YouTube Videos Generator - Git Upload
echo ============================================

REM Move to project directory
cd /d C:\VISWA\0000_PYTHON_APPS\Youtube_VIDEOS_GENERATION

echo.
echo 📂 Current directory:
cd

REM Initialize git if not already
if not exist ".git" (
    echo 🔧 Initializing Git repository...
    git init
)

REM Ensure .gitignore exists
if not exist ".gitignore" (
    echo ❌ ERROR: .gitignore not found!
    echo Please create .gitignore before continuing.
    pause
    exit /b
)

echo.
echo 🔍 Checking ignored files...
git status --ignored

echo.
echo ➕ Adding allowed files to Git...
git add .

echo.
echo 📌 Git status (review before commit):
git status

echo.
set /p commitmsg="📝 Enter commit message: "

if "%commitmsg%"=="" (
    echo ❌ Commit message cannot be empty!
    pause
    exit /b
)

git commit -m "%commitmsg%"

REM Set branch to main
git branch -M main

REM Add remote if missing
git remote | findstr origin >nul
if errorlevel 1 (
    echo 🔗 Adding GitHub remote...
    git remote add origin https://github.com/vsrepalle/youtube_videos_ver1.git
)

echo.
echo 🚀 Pushing to GitHub...
git push -u origin main

echo.
echo ✅ Upload complete!
echo Check: https://github.com/vsrepalle/youtube_videos_ver1
echo ============================================
pause
