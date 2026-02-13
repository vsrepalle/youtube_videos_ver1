import requests
import os

def upload_video_to_facebook(video_path, metadata):
    # --- CONFIGURATION ---
    # It's better to store these in environment variables for security
    PAGE_ID = "25435512632737340"
    ACCESS_TOKEN = "1512518240319241|Xp7L-SYRyNptQH4JSp--aWBcyNQ"
    
    # Facebook uses a different host for video uploads
    url = f"https://graph-video.facebook.com/v19.0/{PAGE_ID}/videos"
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return

    # Payload with caption and title
    payload = {
        'description': f"{metadata['hook_text']}\n\n{metadata['details']}\n\n{' '.join(metadata['tags'])}",
        'title': metadata['headline'],
        'access_token': ACCESS_TOKEN
    }

    # Binary file data
    files = {
        'source': open(video_path, 'rb')
    }

    print(f"📡 Uploading to Facebook Page {PAGE_ID}...")

    try:
        response = requests.post(url, data=payload, files=files)
        result = response.json()

        if "id" in result:
            print(f"✅ Success! Facebook Video ID: {result['id']}")
        else:
            print(f"❌ Upload Failed: {result.get('error', {}).get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"⚠️ Connection Error: {e}")
    finally:
        files['source'].close()

# Integration with your existing metadata
if __name__ == "__main__":
    # Example metadata from your JSON
    example_meta = {
        "hook_text": "Is India now UNSTOPPABLE?",
        "headline": "INDIA'S HISTORIC 93-RUN BLITZ!",
        "details": "India crushed Namibia by 93 runs—their biggest-ever T20 World Cup win.",
        "tags": ["#TrendWaveNow", "#Cricket2026"]
    }
    upload_video_to_facebook("TrendWave_Final_V37.mp4", example_meta)