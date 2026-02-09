import os
import sys
import argparse
import traceback
import google.auth.transport.requests
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def auth():
    token_path = os.path.join(BASE_DIR, "token.json")
    secrets_path = os.path.join(BASE_DIR, "client_secrets.json")

    if not os.path.exists(secrets_path):
        raise FileNotFoundError(f"❌ client_secrets.json NOT FOUND at {secrets_path}")

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)

def upload(video_path, title, description, tags):
    print(f"📤 Uploading: {title}")
    youtube = auth()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags.split(","),
                "categoryId": "24" 
            },
            "status": {
                "privacyStatus": "private"
            }
        },
        media_body=MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    )
    response = request.execute()
    print(f"✅ SUCCESS! Video ID: {response['id']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="tune with us for more such news")
    parser.add_argument("--tags", default="news, shorts")
    
    args = parser.parse_args()
    try:
        upload(args.file, args.title, args.description, args.tags)
    except Exception as e:
        traceback.print_exc()
    input("\nPress ENTER to close...")