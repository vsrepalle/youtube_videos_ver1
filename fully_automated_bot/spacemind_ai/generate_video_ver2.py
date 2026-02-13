import os
import json
import numpy as np
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
import video_effects as fx

# --- FEATURE FIX: IMAGEMAGICK PATH ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

try:
    from stage3_upload import upload_from_json
except ImportError:
    upload_from_json = None

W, H = 1080, 1920
BGM_PATH = "bg_music.mp3"
DEFAULT_BG = "default_bg.jpg"

def get_background_clip(item, duration):
    """Loads background based on JSON path or creates a gradient."""
    img_path = item.get("image_path")
    if img_path and os.path.exists(img_path):
        return ImageClip(img_path).resize(height=H).set_duration(duration)
    return ImageClip(np.zeros((H, W, 3))).set_duration(duration) # Simple black if none

def generate_video_and_upload(json_file):
    if not os.path.exists(json_file): return

    with open(json_file, "r", encoding="utf-8") as f:
        items = json.load(f)

    for i, item in enumerate(items):
        # --- FEATURE FIX: ACCESS ALL JSON FIELDS ---
        video_filename = item.get("video_name", f"Video_{i}.mp4")
        hook = item.get("hook_text", "")
        headline = item.get("headline", "")
        details = item.get("details", "")
        
        # Accessing YouTube Metadata Feature
        yt_meta = item.get("youtube_metadata", {})
        yt_title = yt_meta.get("title", headline)
        hashtags = " ".join(yt_meta.get("hashtags", []))

        tts_text = f"{hook}. {headline}. {details}"
        tts_file = f"voice_{i}.mp3"
        gTTS(text=tts_text, lang="en").save(tts_file)
        voice = AudioFileClip(tts_file)

        bg_layer = get_background_clip(item, voice.duration)
        
        # --- FEATURE FIX: TEXT OVERLAYS ---
        hook_clip = TextClip(hook, fontsize=90, color="yellow", font="Arial-Bold", 
                             method="caption", size=(W-100, None)).set_duration(voice.duration).set_position(("center", 200))
        
        detail_clip = TextClip(details, fontsize=50, color="white", font="Arial",
                               method="caption", size=(W-150, None)).set_duration(voice.duration).set_position(("center", 600))

        # --- FEATURE FIX: FINAL CTA (STRICTLY LAST SCENE) ---
        cta_text = "Tune with us for more such news"
        cta_clip = TextClip(cta_text, fontsize=60, color="cyan", font="Arial-Bold"
                           ).set_start(voice.duration - 3).set_duration(3).set_position(("center", 1600))

        final_video = CompositeVideoClip([bg_layer, hook_clip, detail_clip, cta_clip], size=(W, H)).set_audio(voice)
        
        # Write file as Private (handled by metadata in upload script)
        final_video.write_videofile(video_filename, fps=24, codec="libx264")

        print(f"✅ Video Generated: {video_filename}")
        print(f"📌 Metadata Prepared: {yt_title} | {hashtags}")

        if upload_from_json:
            upload_from_json(json_file)

if __name__ == "__main__":
    generate_video_and_upload("news_data.json")