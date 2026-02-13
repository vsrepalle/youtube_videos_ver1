import os, json
import numpy as np
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
import video_effects as fx 

# --- CRITICAL FIX: ImageMagick Path ---
# Ensure this points to your specific Magick.exe
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

try:
    from stage3_upload import upload_from_json
except ImportError:
    upload_from_json = None

OUTPUT_VIDEO = "TrendWave_Final_V37.mp4"
BGM_PATH = "bg_music.mp3"
W, H = 1080, 1920

def get_safe_background(voice_duration):
    """Checks for temp_bg.jpg; if missing, creates a dark blue placeholder."""
    bg_image = "temp_bg.jpg"
    if os.path.exists(bg_image):
        return ImageClip(bg_image).resize(height=H).set_duration(voice_duration)
    
    # Failsafe: Create a simple dark gradient/solid background
    print(f"⚠️ Warning: '{bg_image}' not found. Using a dark placeholder.")
    placeholder = np.zeros((H, W, 3), dtype=np.uint8)
    placeholder[:, :] = [15, 15, 35] # Deep space blue
    return ImageClip(placeholder).set_duration(voice_duration)

def generate_video_and_upload(json_file):
    if not os.path.exists(json_file): return
    with open(json_file, "r", encoding="utf-8") as f: 
        items = json.load(f)

    # File Existence Check
    if os.path.exists(OUTPUT_VIDEO):
        choice = input(f"⚡ '{OUTPUT_VIDEO}' exists. [U]pload or [R]e-create? ").strip().lower()    
        if choice in ['u', 'y']:
            if upload_from_json: upload_from_json(json_file)
            return
        elif choice != 'r': return

    scenes = []
    
    for i, item in enumerate(items):
        # 1. Voice Generation
        tts_text = f"{item['hook_text']}. {item['headline']}. {item['details']}"
        tts_file = f"voice_{i}.mp3"
        gTTS(text=tts_text, lang='en').save(tts_file)
        voice = AudioFileClip(tts_file)
        
        # 2. Background with Failsafe
        bg_layer = get_safe_background(voice.duration)
        bg_layer = fx.apply_ken_burns(bg_layer, zoom_ratio=0.05)
        
        # 3. Sentence-by-Sentence Text
        scrolling_text = fx.create_sentence_scrolling(item['details'], voice.duration, W, H)
        
        # 4. Header Hook
        hook = TextClip(item['hook_text'], fontsize=100, color='yellow', font='Arial-Bold', 
                        method='caption', size=(W-100, 300)).set_position(('center', 200)).set_duration(voice.duration)

        scene = CompositeVideoClip([bg_layer, hook, scrolling_text], size=(W, H)).set_audio(voice)
        scenes.append(scene)

    final_video = concatenate_videoclips(scenes, method="compose")
    
    # 5. Background Music
    if os.path.exists(BGM_PATH):
        final_video = fx.add_background_audio(final_video, BGM_PATH)

    # LAST SCENE ONLY: CTA
    # Pulling 'tune with us' choice from your preferences
    cta_text = "Tune with us for more such news"
    cta = TextClip(cta_text, fontsize=55, color='white', font='Arial-Bold'
                  ).set_start(final_video.duration - 3.5).set_duration(3.5).set_position(('center', 1600))
    
    final_comp = CompositeVideoClip([final_video, cta])
    
    # Rendering as Private (as per instructions)
    final_comp.write_videofile(OUTPUT_VIDEO, fps=24, codec="libx264")
    
    if upload_from_json:
        upload_from_json(json_file)

if __name__ == "__main__":
    generate_video_and_upload("news_data.json")