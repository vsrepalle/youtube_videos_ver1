import os
import json
import argparse
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# YouTube API Setup
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
    credentials = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=credentials)

def upload_from_json(json_file):
    if not os.path.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # FIXED: Logic to find the video file path
    # If "video_name" is missing, use the "id" + ".mp4"
    video_filename = data.get("video_name") or f"{data.get('id', 'TrendWave_Update')}.mp4"
    video_path = os.path.abspath(video_filename)

    # Error handling for the NoneType/Path issue
    if not video_path or not os.path.exists(video_path):
        print(f"❌ Video file NOT FOUND at: {video_path}")
        print("💡 Make sure Stage 2 (Rendering) finished successfully.")
        return

    youtube = get_authenticated_service()

    # Metadata setup
    request_body = {
        "snippet": {
            "title": data.get("topic", "Cricket Update"),
            "description": f"Latest news update.\nTune with us for more such news.",
            "tags": ["cricket", "news", "trendwave"],
            "categoryId": "17" # Sports
        },
        "status": {
            "privacyStatus": "private",  # ALWAYS PRIVATE BY DEFAULT
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    print(f"🚀 Uploading: {video_filename}...")
    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"📈 Uploading... {int(status.progress() * 100)}%")

    print(f"✅ Upload Complete! Video ID: {response['id']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="cricket_updates_feb11.json", help="Path to JSON file")
    args = parser.parse_args()
    
    upload_from_json(args.json)