import os, json, re, logging, sys
import numpy as np
from PIL import Image, ImageFilter
from gtts import gTTS
from icrawler.builtin import BingImageCrawler
from moviepy.config import change_settings

# YouTube API Imports
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

# --- 1. CONFIGURATION ---
IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})

from moviepy.editor import (
    ImageClip, TextClip, CompositeVideoClip, 
    concatenate_videoclips, AudioFileClip, CompositeAudioClip
)
import moviepy.video.fx.all as vfx

# Silence Logs
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger('icrawler').setLevel(logging.CRITICAL)

VIDEO_SIZE = (1920, 1080)
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_landscape_frame(path):
    try:
        img = Image.open(path).convert("RGB")
        bg = img.resize(VIDEO_SIZE, Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(radius=30))
        ratio = img.width / img.height
        target_h = 1080
        target_w = int(target_h * ratio)
        if target_w > 1920: target_w = 1920
        img_res = img.resize((target_w, int(target_w/ratio)), Image.Resampling.LANCZOS)
        bg.paste(img_res, ((VIDEO_SIZE[0] - img_res.width) // 2, (VIDEO_SIZE[1] - img_res.height) // 2))
        return np.array(bg)
    except: return np.zeros((1080, 1920, 3), dtype="uint8")

def publish_to_youtube(file_path, metadata):
    """Authenticates and uploads video to YouTube as Private."""
    print("\n🔐 Authenticating with Google...")
    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
    credentials = flow.run_local_server(port=0)
    youtube = build("youtube", "v3", credentials=credentials)

    body = {
        "snippet": {
            "title": metadata.get("title", "TrendWave News Update"),
            "description": metadata.get("description", "Tune with us for more such news."),
            "categoryId": "22"
        },
        "status": {"privacyStatus": "private"}
    }

    print(f"📡 Uploading {file_path}...")
    insert_request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(file_path, chunksize=1024*1024, resumable=True)
    )

    response = None
    while response is None:
        status, response = insert_request.next_chunk()
        if status:
            print(f"📤 Progress: {int(status.progress() * 100)}%")
    print(f"✅ Published! Video ID: {response['id']}")

def run_production(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    video_path = data.get("video_name", "TrendWave_Final.mp4")
    
    if not os.path.exists(video_path) or input(f"📂 '{video_path}' exists. Re-create? (y/n): ").lower() == 'y':
        clips = []
        sub_bar = TextClip(txt="Please subscribe TrendWave Now", font="Arial-Bold", fontsize=40, 
                           color="white", bg_color="red", size=(1920, 60)).set_position(("center", 1020))

        for i, scene in enumerate(data["scenes"]):
            img_dir = f"media_bank/scene_{i}"
            if not os.path.exists(img_dir) or len(os.listdir(img_dir)) < 1:
                os.makedirs(img_dir, exist_ok=True)
                crawler = BingImageCrawler(storage={'root_dir': img_dir})
                for k in [f"{scene['star_name']} 2026", "cricket highlights", "stadium"]:
                    crawler.crawl(keyword=k, max_num=1)
                del crawler
            
            print(f"✅ Scene {i+1} media ready.")
            if input("🤔 Continue? (y/n): ").lower() != 'y': return

            img_files = [os.path.join(img_dir, f) for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.png'))][:3]
            gTTS(text=re.sub(r"\[.*?\]", "", scene["text"]), lang='en').save(f"v_{i}.mp3")
            audio = AudioFileClip(f"v_{i}.mp3").fx(vfx.speedx, 1.15)
            duration = audio.duration + 0.5

            txt = TextClip(txt=scene["text"], font="Arial-Bold", fontsize=48, color="yellow", bg_color="black", method='caption', size=(1500, None)).set_duration(duration).set_position(lambda t: ('center', 1080 - (400 * t / duration)))
            
            scene_clips = [ImageClip(get_landscape_frame(p)).set_duration(duration/len(img_files)).set_start(idx*(duration/len(img_files))) for idx, p in enumerate(img_files)]
            clips.append(CompositeVideoClip([CompositeVideoClip(scene_clips), txt, sub_bar.set_duration(duration)]).set_audio(audio))

        concatenate_videoclips(clips, method="compose").write_videofile(video_path, fps=24, logger=None)

    if input(f"🚀 Publish '{video_path}' to YouTube? (y/n): ").lower() == 'y':
        publish_to_youtube(video_path, data.get("metadata", {}))

if __name__ == "__main__":
    run_production("news_production.json")