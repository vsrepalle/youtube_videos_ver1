import os, sys, json, argparse
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import google.auth.transport.requests

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def auth():
    creds = None
    token_file = "token.json"
    secrets_file = "client_secrets.json"

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            if not os.path.exists(secrets_file):
                print(f"❌ ERROR: Missing '{secrets_file}'!")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_file, "w") as token:
            token.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)

def upload_from_json(json_path):
    # Load JSON Data
    if not os.path.exists(json_path):
        print(f"❌ ERROR: JSON file not found at {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract Metadata
    meta = data.get("youtube_metadata", {})
    video_path = data.get("file") # Path to the rendered MP4
    title = meta.get("title", "TrendWave Update")
    description = meta.get("description", "Tune with us for more such news")
    # Convert list of tags to Python list if it's already a list, or split if it's a string
    tags = meta.get("tags", ["news", "shorts"])
    if isinstance(tags, str):
        tags = tags.split(",")

    if not os.path.exists(video_path):
        print(f"❌ ERROR: Video file {video_path} not found!")
        return

    youtube = auth()
    print(f"📤 Uploading: {title}...")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "24" # Entertainment
        },
        "status": {
            "privacyStatus": meta.get("privacyStatus", "private") # Always private by default
        }
    }
    
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    )
    
    response = request.execute()
    print(f"🎉 SUCCESS! Video ID: {response['id']}")
    print(f"🔗 Link: https://youtu.be/{response['id']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="Path to the JSON metadata file")
    args = parser.parse_args()
    upload_from_json(args.json)