@echo off
:: Change directory to where your scripts are located
cd /d "C:\VISWA\0000_PYTHON_APPS\Youtube_VIDEOS_GENERATION"

:: Step 1: Fetch Shorts-specific assets
python bulk_fetcher_shorts.py stars_data.json && (
    echo 🎬 Shorts assets ready. Generating video...
    :: Step 2: Create Video
    python generate_video.py stars_data.json
) && (
    echo ☁️ Video created. Uploading...
    :: Step 3: Upload (Ensure publish_to_youtube.py is configured)
    :: python publish_to_youtube.py (This is invoked by generate_video.py now, so no need here)
)

echo Pipeline Finished.
pause