@echo off
echo 🤖 STEP 1: Harvesting Content from Gemini AI...
python generate_educational_json.py

echo.
echo 🎬 STEP 2: Producing Videos and Preparing Uploads...
:: CHANGE THIS LINE to match your actual production script name
python create_text_videos_upload_to_youtube.py 

pause