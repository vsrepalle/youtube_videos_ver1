import os
import json
import re
import pickle
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import (
    VideoFileClip, CompositeVideoClip, concatenate_videoclips,
    ImageClip, AudioFileClip, CompositeAudioClip, afx
)
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ✅ PILLOW COMPATIBILITY
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

# ✅ CONFIG IMPORTS
from config import (
    PEXELS_API_KEY, PIXABAY_API_KEY, DOWNLOAD_DIR, OUTPUT_DIR, 
    VIDEO_SIZE, FPS, MIN_SCENE_DURATION, FONT_SIZE, FONT_COLOR, 
    STROKE_COLOR, STROKE_WIDTH, BOTTOM_MARGIN
)

# Constants
INPUT_JSON = "scenes.json"
OUTPUT_VIDEO = os.path.join(OUTPUT_DIR, "final_video.mp4")
AUDIO_DIR = os.path.join(DOWNLOAD_DIR, "audio")
VIDEO_CACHE_DIR = os.path.join(DOWNLOAD_DIR, "videos")
BGM_PATH = "background.mp3"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

for d in [DOWNLOAD_DIR, OUTPUT_DIR, AUDIO_DIR, VIDEO_CACHE_DIR]:
    os.makedirs(d, exist_ok=True)

# =====================
# VIDEO & AUDIO LOGIC
# =====================

def generate_tts(text, scene_id):
    """Cleans text of [HOOK] tags for audio but keeps them for display."""
    audio_path = os.path.join(AUDIO_DIR, f"scene_{scene_id}.mp3")
    clean_text = re.sub(r'\[.*?\]', '', text).strip()
    
    if not os.path.exists(audio_path):
        print(f"🎙️ Generating speech: {clean_text[:30]}...")
        gTTS(text=clean_text, lang='en').save(audio_path)
    return audio_path

def fetch_video(query):
    """Fetches from local cache, then Pexels, then Pixabay."""
    safe_query = query.replace(' ', '_').lower()
    filename = os.path.join(VIDEO_CACHE_DIR, f"{safe_query}.mp4")
    if os.path.exists(filename): return filename

    # Pexels Try
    try:
        url = "https://api.pexels.com/videos/search"
        r = requests.get(url, headers={"Authorization": PEXELS_API_KEY}, 
                         params={"query": query, "per_page": 1, "orientation": "portrait"}, timeout=15)
        videos = r.json().get("videos", [])
        if videos:
            link = max(videos[0]["video_files"], key=lambda v: v["height"])["link"]
            with requests.get(link, stream=True) as vr:
                with open(filename, "wb") as f:
                    for chunk in vr.iter_content(1024*1024): f.write(chunk)
            return filename
    except: pass

    # Pixabay Try
    try:
        url = "https://pixabay.com/api/videos/"
        r = requests.get(url, params={"key": PIXABAY_API_KEY, "q": query, "per_page": 1}, timeout=15)
        hits = r.json().get("hits", [])
        if hits:
            link = hits[0]["videos"]["large"]["url"]
            with requests.get(link, stream=True) as vr:
                with open(filename, "wb") as f:
                    for chunk in vr.iter_content(1024*1024): f.write(chunk)
            return filename
    except: pass
    return None

def subtitle_clip(text, duration):
    img = Image.new("RGBA", VIDEO_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("arial.ttf", FONT_SIZE)
    except: font = ImageFont.load_default()
    
    words = text.split()
    lines, current_line = [], []
    for word in words:
        current_line.append(word)
        if draw.multiline_textbbox((0, 0), " ".join(current_line), font=font)[2] > (VIDEO_SIZE[0] - 100):
            lines.append(" ".join(current_line[:-1]))
            current_line = [word]
    lines.append(" ".join(current_line))
    wrapped_text = "\n".join(lines)
    bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align="center")
    x, y = (VIDEO_SIZE[0] - (bbox[2]-bbox[0])) // 2, VIDEO_SIZE[1] - BOTTOM_MARGIN - (bbox[3]-bbox[1])
    draw.multiline_text((x, y), wrapped_text, font=font, fill=FONT_COLOR, align="center", stroke_width=STROKE_WIDTH, stroke_fill=STROKE_COLOR)
    return ImageClip(np.array(img)).set_duration(duration)

# =====================
# YOUTUBE UPLOAD LOGIC
# =====================

def upload_to_youtube(file_path, title, description, tags):
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token: creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token: pickle.dump(creds, token)
    
    youtube = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {"title": title, "description": description, "tags": tags.split(","), "categoryId": "17"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    print(f"🚀 Uploading to YouTube: {title}")
    youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    print("✅ Upload Complete!")

# =====================
# MAIN EXECUTION
# =====================

def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    final_clips = []
    bgm = AudioFileClip(BGM_PATH).volumex(0.12) if os.path.exists(BGM_PATH) else None

    for idx, scene in enumerate(data["scenes"], start=1):
        text, query = scene["text"], scene["search_key"]
        audio_path = generate_tts(text, idx)
        voice = AudioFileClip(audio_path)
        duration = max(MIN_SCENE_DURATION, voice.duration)

        v_path = fetch_video(query)
        if not v_path: continue
        
        raw = VideoFileClip(v_path).without_audio().subclip(0, duration).resize(newsize=VIDEO_SIZE)
        clip = raw.set_audio(voice)
        sub = subtitle_clip(text, duration)
        final_clips.append(CompositeVideoClip([clip, sub], size=VIDEO_SIZE).set_duration(duration))

    final_video = concatenate_videoclips(final_clips, method="compose")
    if bgm:
        looped_bgm = bgm.fx(afx.audio_loop, duration=final_video.duration)
        final_video = final_video.set_audio(CompositeAudioClip([final_video.audio, looped_bgm]))

    final_video.write_videofile(OUTPUT_VIDEO, fps=FPS, codec="libx264", audio_codec="aac", preset="ultrafast")
    
    # --- INVOKE UPLOAD ---
    upload_to_youtube(
        OUTPUT_VIDEO, 
        data['metadata']['title'], 
        data['metadata']['description'], 
        data['metadata']['tags']
    )
    print("💡 Suggestion: Cricket news is performing amazingly well. We concluded with the suggestion to use T20 World Cup topics!")

if __name__ == "__main__":
    main()