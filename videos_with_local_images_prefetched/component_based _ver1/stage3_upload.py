import os, sys, argparse
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

    # Check if we already have a saved token
    if os.path.exists(token_file):
        print("💡 Found existing 'token.json'.")
        use_existing = input("❓ Use existing session? (y) or re-authenticate (n): ").lower()
        if use_existing == 'y':
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # If no valid creds, or user chose 'n', run the login flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Session expired. Refreshing token...")
            creds.refresh(google.auth.transport.requests.Request())
        else:
            print("🔑 No valid session found. Opening browser for login...")
            if not os.path.exists(secrets_file):
                print(f"❌ ERROR: Missing '{secrets_file}'! Please download it from Google Cloud Console.")
                sys.exit(1)
            
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_file, "w") as token:
            token.write(creds.to_json())
            print(f"✅ New '{token_file}' created and saved.")

    return build("youtube", "v3", credentials=creds)

def upload(video_path, title, description, tags):
    if not os.path.exists(video_path):
        print(f"❌ ERROR: Video file not found at {video_path}")
        return

    youtube = auth()
    print(f"📤 Uploading: {title}...")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags.split(","),
            "categoryId": "24" 
        },
        "status": {
            "privacyStatus": "private" # 🔒 Locked as private as requested
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
    parser.add_argument("--file", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="tune with us for more such news")
    parser.add_argument("--tags", default="news, shorts")
    args = parser.parse_args()
    upload(args.file, args.title, args.description, args.tags)