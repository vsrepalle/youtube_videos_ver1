@echo off
echo ================================
echo  YOUTUBE AUTOMATION GIT UPLOAD
echo  (PY + IMAGE FILES ONLY)
echo ================================

REM --- STEP 1: Initialize git if not already ---
if not exist ".git" (
    echo Initializing git repository...
    git init
)

REM --- STEP 2: Set remote (force correct repo) ---
git remote remove origin 2>nul
git remote add origin https://github.com/vsrepalle/Youtube_Automation.git

REM --- STEP 3: Clean staging area ---
git reset

REM --- STEP 4: Add ONLY Python + Images ---
echo Adding Python files...
git add *.py
git add **/*.py

echo Adding image files...
git add *.jpg *.jpeg *.png *.webp
git add **/*.jpg **/*.jpeg **/*.png **/*.webp

REM --- STEP 5: Commit ---
git commit -m "Update automation scripts and image assets"

REM --- STEP 6: Ensure branch is main ---
git branch -M main

REM --- STEP 7: Pull safely (in case repo is not empty) ---
git pull origin main --rebase --allow-unrelated-histories

REM --- STEP 8: Push to GitHub ---
git push -u origin main

echo ================================
echo  ✅ UPLOAD COMPLETE
echo ================================
pause
