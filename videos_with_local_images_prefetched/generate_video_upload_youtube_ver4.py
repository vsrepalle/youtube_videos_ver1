import os, json, re, logging
import numpy as np
from PIL import Image, ImageFilter
from gtts import gTTS
from icrawler.builtin import BingImageCrawler
from moviepy.config import change_settings

# --- 1. CRITICAL CONFIG & PATHS ---
IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})

from moviepy.editor import (
    ImageClip, TextClip, CompositeVideoClip, 
    concatenate_videoclips, AudioFileClip, CompositeAudioClip
)
import moviepy.video.fx.all as vfx

# Silence console logs
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger('icrawler').setLevel(logging.CRITICAL)

# Long-form 16:9 Resolution
VIDEO_SIZE = (1920, 1080) 

def get_landscape_frame(path):
    """Processes images for 16:9 format with blurred backgrounds."""
    try:
        img = Image.open(path).convert("RGB")
        bg = img.resize(VIDEO_SIZE, Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(radius=30))
        
        ratio = img.width / img.height
        target_h = 1080
        target_w = int(target_h * ratio)
        
        if target_w > 1920:
            target_w = 1920
            target_h = int(target_w / ratio)
            
        img_res = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        bg.paste(img_res, ((VIDEO_SIZE[0] - img_res.width) // 2, (VIDEO_SIZE[1] - img_res.height) // 2))
        return np.array(bg)
    except:
        return np.zeros((1080, 1920, 3), dtype="uint8")

def generate_video(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    output = data.get("video_name", "T20_World_Cup_9Feb.mp4")
    if os.path.exists(output):
        if input(f"📂 '{output}' found. Re-create? (y/n): ").lower() != 'y':
            return

    clips = []
    audio_sfx = []
    current_time = 0

    # Subscription Bar
    sub_bar = TextClip(txt="Please subscribe TrendWave Now", font="Arial-Bold", fontsize=40, 
                       color="white", bg_color="red", size=(1920, 60)).set_position(("center", 1020))

    for i, scene in enumerate(data["scenes"]):
        # Image Downloader
        img_dir = f"media_bank/t20_scene_{i}"
        if not os.path.exists(img_dir) or len(os.listdir(img_dir)) < 1:
            os.makedirs(img_dir, exist_ok=True)
            crawler = BingImageCrawler(storage={'root_dir': img_dir})
            # Rotation keys for variety
            keys = [f"{scene['star_name']} T20 2026", f"{scene['star_name']} action", "Cricket stadium lights"]
            for k in keys:
                crawler.crawl(keyword=k, max_num=1)
            del crawler
            
            print(f"✅ Media ready for: {scene['star_name']}")
            if input(f"🤔 Everything looks good. Start rendering scene {i+1}? (y/n): ").lower() != 'y':
                return

        img_files = [os.path.join(img_dir, f) for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.png'))][:3]
        
        # Audio
        voice_file = f"voice_{i}.mp3"
        gTTS(text=re.sub(r"\[.*?\]", "", scene["text"]), lang='en').save(voice_file)
        audio = AudioFileClip(voice_file).fx(vfx.speedx, 1.15)
        duration = audio.duration + 0.5

        # Scrolling Subtitles (Moves from bottom edge upward)
        txt_overlay = (TextClip(txt=scene["text"], font="Arial-Bold", fontsize=45, color="yellow", 
                               bg_color="black", method='caption', size=(1600, None))
                       .set_duration(duration)
                       .set_position(lambda t: ('center', 1080 - (350 * t / duration))))

        # Composite Scene
        sub_clips = [ImageClip(get_landscape_frame(p)).set_duration(duration/len(img_files)).set_start(idx*(duration/len(img_files))) 
                     for idx, p in enumerate(img_files)]
        
        scene_base = CompositeVideoClip([CompositeVideoClip(sub_clips), txt_overlay, sub_bar.set_duration(duration)])
        clips.append(scene_base.set_audio(audio))

        if i > 0 and os.path.exists("whoosh.mp3"):
            audio_sfx.append(AudioFileClip("whoosh.mp3").set_start(current_time))
        current_time += duration

    # Final Render
    final_video = concatenate_videoclips(clips, method="compose")
    tracks = [final_video.audio] + audio_sfx
    if os.path.exists("background.mp3"):
        tracks.append(AudioFileClip("background.mp3").volumex(0.08).set_duration(final_video.duration))
    
    final_video.set_audio(CompositeAudioClip(tracks)).write_videofile(output, fps=24, logger=None)
    print(f"🚀 Long-form Video Complete: {output}")

if __name__ == "__main__":
    generate_video("news_production_video.json")