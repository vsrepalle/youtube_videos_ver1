import os
import json
import argparse
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

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
        data_raw = json.load(f)

    items = data_raw if isinstance(data_raw, list) else [data_raw]
    data = items[0]

    video_filename = data.get("video_name", "SpaceMind_Final.mp4")
    video_path = os.path.abspath(video_filename)

    if not os.path.exists(video_path):
        print(f"❌ Video NOT FOUND: {video_path}")
        return

    youtube = get_authenticated_service()

    yt_meta = data.get("youtube_metadata", {})
    title = yt_meta.get("title", data.get("headline", "SpaceMind AI Update"))
    description = yt_meta.get("description", data.get("details", ""))
    hashtags = yt_meta.get("hashtags", [])

    full_description = description + "\n\n" + " ".join(hashtags)

    request_body = {
        "snippet": {
            "title": title,
            "description": full_description,
            "tags": hashtags,
            "categoryId": "28"  # Science & Technology
        },
        "status": {
            "privacyStatus": "private",
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
    parser.add_argument("--json", default="news_data.json")
    args = parser.parse_args()
    upload_from_json(args.json)
