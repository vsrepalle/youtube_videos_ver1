import os
import sys
import json
import shutil
import subprocess
import numpy as np
from gtts import gTTS
from icrawler.builtin import BingImageCrawler
from PIL import Image, ImageDraw, ImageFont

# --- 🛠️ SYSTEM PATCHES ---
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# MoviePy Imports
try:
    from moviepy.editor import ImageClip, concatenate_videoclips, CompositeVideoClip, AudioFileClip
except ImportError:
    from moviepy import ImageClip, concatenate_videoclips, CompositeVideoClip, AudioFileClip

# --- 🚀 HELPERS ---
def make_even(n):
    """Ensures dimensions are divisible by 2 for H.264 codec."""
    return int(n) if int(n) % 2 == 0 else int(n) - 1

def run_production(json_file):
    if not os.path.exists(json_file):
        print(f"❌ JSON file {json_file} not found.")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    video_name = data.get('video_name', 'DHURANDHAR_NEWS_UPDATE.mp4')
    video_path = os.path.abspath(video_name)
    assets_dir = os.path.abspath('temp_assets')

    if input(f"\n🎥 Create/Re-render {video_name}? (y/n): ").lower() == 'y':
        if os.path.exists(assets_dir): shutil.rmtree(assets_dir)
        os.makedirs(assets_dir, exist_ok=True)
        
        all_scene_clips = []

        for scene in data['scenes']:
            sid, txt, query = scene['id'], scene['text'], scene['query']
            print(f"🎬 Scene {sid}: {txt[:30]}...")
            
            # 1. Download Image
            scene_dir = os.path.join(assets_dir, f"s_{sid}")
            os.makedirs(scene_dir, exist_ok=True)
            crawler = BingImageCrawler(storage={'root_dir': scene_dir})
            crawler.crawl(keyword=query, max_num=1)
            
            # 2. Generate Audio
            audio_path = os.path.join(assets_dir, f"audio_{sid}.mp3")
            tts = gTTS(text=txt, lang='en')
            tts.save(audio_path)
            audio = AudioFileClip(audio_path)

            # 3. Create Clip
            img_files = [os.path.join(scene_dir, f) for f in os.listdir(scene_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
            if img_files:
                img_clip = ImageClip(img_files[0]).set_duration(audio.duration).set_audio(audio)
                
                # Resize to common HD, ensuring even numbers
                w, h = make_even(1280), make_even(720)
                img_clip = img_clip.resize(newsize=(w, h))
                all_scene_clips.append(img_clip)

        # --- ⭐ THE FIX: DEFINING 'final' ---
        if all_scene_clips:
            print("🔗 Concatenating scenes into final video...")
            final = concatenate_videoclips(all_scene_clips, method="compose")
            
            # 4. Write File
            final.write_videofile(
                video_path, 
                fps=24, 
                codec="libx264", 
                audio_codec="aac",
                ffmpeg_params=["-pix_fmt", "yuv420p"]
            )
            print(f"✅ Video ready: {video_path}")
            os.startfile(video_path)
        else:
            print("❌ No clips were generated. Check your image queries.")
            return

    # --- 🚀 HANDOFF TO UPLOADER ---
    if os.path.exists(video_path) and input(f"\n🚀 Send to Uploader? (y/n): ").lower() == 'y':
        uploader_script = os.path.join(os.path.dirname(__file__), "upload_video.py")
        if os.path.exists(uploader_script):
            title = f"Dhurandhar News | {data.get('news_date', 'Today')}"
            subprocess.Popen([sys.executable, uploader_script, video_path, title])
            print("📡 Handoff complete. tune with us for more such news")
        else:
            print(f"❌ Uploader script not found at: {uploader_script}")

if __name__ == "__main__":
    # Ensure this matches your JSON filename
    run_production("bollywood_scenes.json")