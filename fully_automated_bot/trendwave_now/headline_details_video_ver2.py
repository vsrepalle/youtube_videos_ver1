import os, json
from gtts import gTTS
from moviepy.editor import *
import video_effects as fx # Importing our new library
try:
    from stage3_upload import upload_from_json
except ImportError:
    upload_from_json = None

OUTPUT_VIDEO = "TrendWave_Final_V37.mp4"
BGM_PATH = "bg_music.mp3"

def generate_video_and_upload(json_file):
    if not os.path.exists(json_file): return
    with open(json_file, "r") as f: items = json.load(f)

    # User Prompt for Existing Files
    if os.path.exists(OUTPUT_VIDEO):
        choice = input(f"⚡ '{OUTPUT_VIDEO}' exists. [U]pload or [R]e-create? ").strip().lower()
        if choice in ['u', 'y']:
            if upload_from_json: upload_from_json(json_file)
            return
        elif choice != 'r': return

    W, H = 1080, 1920
    scenes = []
    
    for i, item in enumerate(items):
        # 1. Voice Generation
        tts_text = f"{item['hook_text']}. {item['headline']}. {item['details']}"
        tts_file = f"voice_{i}.mp3"
        gTTS(text=tts_text, lang='en').save(tts_file)
        voice = AudioFileClip(tts_file)
        
        # 2. Background with Zoom Effect
        bg_image = "temp_bg.jpg" # Logic to fetch image should be here
        bg_layer = ImageClip(bg_image).resize(height=H).set_duration(voice.duration)
        bg_layer = fx.apply_ken_burns(bg_layer, zoom_ratio=0.05)
        
        # 3. Sentence-by-Sentence Text
        scrolling_text = fx.create_sentence_scrolling(item['details'], voice.duration, W, H)
        
        # 4. Header Hook
        hook = TextClip(item['hook_text'], fontsize=100, color='yellow', font='Arial-Bold', method='caption', size=(W-100, 300)).set_position(('center', 200)).set_duration(voice.duration)

        scene = CompositeVideoClip([bg_layer, hook, scrolling_text], size=(W, H)).set_audio(voice)
        scenes.append(scene)

    final_video = concatenate_videoclips(scenes, method="compose")
    
    # 5. Add Background Music (from our py file)
    final_video = fx.add_background_audio(final_video, BGM_PATH)

    # LAST SCENE ONLY: CTA
    cta = TextClip("Tune with us for more such news", fontsize=55, color='white', font='Arial-Bold').set_start(final_video.duration - 3.5).set_duration(3.5).set_position(('center', 1600))
    
    final_comp = CompositeVideoClip([final_video, cta])
    final_comp.write_videofile(OUTPUT_VIDEO, fps=24, codec="libx264")
    
    if upload_from_json:
        upload_from_json(json_file)

if __name__ == "__main__":
    generate_video_and_upload("news_data.json")