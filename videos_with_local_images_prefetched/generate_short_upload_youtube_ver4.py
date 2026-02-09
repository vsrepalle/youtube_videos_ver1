import os, json, re, logging, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter
from gtts import gTTS
from icrawler.builtin import BingImageCrawler
from moviepy.config import change_settings

# --- 1. CRITICAL WINDOWS CONFIG ---
IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})

from moviepy.editor import (
    ImageClip, TextClip, CompositeVideoClip, 
    concatenate_videoclips, AudioFileClip, vfx
)

# Silence Logs
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger('icrawler').setLevel(logging.CRITICAL)

VIDEO_SIZE = (1920, 1080)

def get_landscape_frame(path):
    """Creates a 16:9 frame with the image centered over a blurred version."""
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
    except:
        return np.zeros((1080, 1920, 3), dtype="uint8")

def publish_to_youtube(file_path, metadata):
    """Placeholder or trigger for your upload_to_youtube.py script."""
    print(f"\n📡 Triggering Upload: {file_path}")
    # (Existing upload code here or call subprocess as before)

def run_production(json_file):
    if not os.path.exists(json_file):
        print(f"❌ JSON file {json_file} not found!")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    video_path = data.get("video_name", "TrendWave_Update.mp4")
    
    # 1. Image & Scene Prep
    clips = []
    # Fixed Subscription Bar (CTA)
    sub_bar = TextClip(txt="Please subscribe TrendWave Now", font="Arial-Bold", fontsize=40, 
                       color="white", bg_color="red", size=(1920, 60)).set_position(("center", 1020))

    for i, scene in enumerate(data["scenes"]):
        img_dir = f"media_bank/scene_{i}"
        if not os.path.exists(img_dir) or len(os.listdir(img_dir)) < 1:
            os.makedirs(img_dir, exist_ok=True)
            crawler = BingImageCrawler(storage={'root_dir': img_dir})
            # Contextual Search: Uses star name + 2026 for latest news feel
            crawler.crawl(keyword=f"{scene['star_name']} 2026 cricket", max_num=3)
            del crawler
        
        print(f"✅ Scene {i+1} media ready for {scene['star_name']}.")
        if input("🤔 Continue? (y/n): ").lower() != 'y': return

        img_files = [os.path.join(img_dir, f) for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.png'))][:3]
        
        # Audio Generation
        voice_file = f"v_{i}.mp3"
        gTTS(text=re.sub(r"\[.*?\]", "", scene["text"]), lang='en').save(voice_file)
        audio = AudioFileClip(voice_file).fx(vfx.speedx, 1.15)
        duration = audio.duration + 0.5

        # --- FIX: SCROLLING SUBTITLES ---
        # Using 'label' and 'scroll' effect to avoid ImageMagick 'caption' hangs
        txt = (TextClip(txt=scene["text"], font="Arial-Bold", fontsize=50, color="yellow", bg_color="black")
               .set_duration(duration)
               .on_color(size=(1920, 150), color=(0,0,0), pos='center') # Background box
               .set_position(('center', 800))
               .fx(vfx.scroll, h=150, w=1920, x_speed=0, y_speed=20)) # Slow upward scroll

        # Build Background
        sub_clips = [ImageClip(get_landscape_frame(p)).set_duration(duration/len(img_files)).set_start(idx*(duration/len(img_files))) 
                     for idx, p in enumerate(img_files)]
        
        scene_comp = CompositeVideoClip([CompositeVideoClip(sub_clips), txt, sub_bar.set_duration(duration)])
        clips.append(scene_comp.set_audio(audio))

    # 2. Final Render
    print("🎬 Starting Final Render (This should move quickly now)...")
    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile(video_path, fps=24, logger='bar', threads=4, preset="ultrafast")
    
    print(f"✅ Video Complete: {video_path}")
    
    # 3. Upload Trigger
    if input(f"🚀 Publish '{video_path}' to YouTube? (y/n): ").lower() == 'y':
        publish_to_youtube(video_path, data.get("metadata", {}))

if __name__ == "__main__":
    run_production("news_production.json")