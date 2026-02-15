import os
from headline_details_video_ver8_multi_channel import get_youtube_service, upload_to_youtube

def manual_mode():
    print("--- 🛠️ MANUAL UPLOAD TOOL ---")
    file_path = input("File path (e.g. video.mp4): ")
    if not os.path.exists(file_path):
        print("Error: File doesn't exist.")
        return

    chan = input("Target Channel (TrendWave Now / SpaceMind AI): ")
    title = input("Video Title: ")
    desc = input("Description: ") + "\n\nTune with us for more such news."
    tags = input("Tags (comma separated): ").split(",")

    meta = {
        "title": title,
        "description": desc,
        "tags": [t.strip() for t in tags],
        "category_id": "22"
    }

    service = get_youtube_service(chan)
    if service:
        upload_to_youtube(service, file_path, meta)

if __name__ == "__main__":
    manual_mode()