import os
import json
import shutil
import subprocess
from gtts import gTTS
from moviepy.editor import *
import moviepy.video.fx.all as vfx
from moviepy.config import change_settings
from icrawler.builtin import BingImageCrawler

# --- 1. CONFIGURATION ---
IM_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IM_PATH})

# News Context: Feb 12, 2026
news_items = [
    {
        "type": "CRICKET UPDATE",
        "headline": "AFGHANISTAN'S SUPER OVER DRAMA!",
        "details": "Historic clash today! Afghanistan pushed South Africa to a DOUBLE Super Over. Gurbaz was the hero, but the Proteas narrowly escaped.",
        "search_key": "Rahmanullah Gurbaz Afghanistan vs South Africa Super Over"
    },
    {
        "type": "MOVIE SHOCKER",
        "headline": "BHAGAM BHAG 2 CASTING TWIST!",
        "details": "Govinda has exited Bhagam Bhag 2. In a surprise move, Manoj Bajpayee is joining Akshay Kumar for this comedy sequel!",
        "search_key": "Akshay Kumar Manoj Bajpayee Bhagam Bhag 2"
    }
]

def fetch_bg_image(query, index):
    temp_dir = f"bg_{index}"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    crawler = BingImageCrawler(storage={'root_dir': temp_dir})
    crawler.crawl(keyword=query, max_num=1, filters=dict(size='large', layout='tall'))
    for file in os.listdir(temp_dir): return os.path.join(temp_dir, file)
    return None

def create_short(items):
    W, H = 1080, 1920 
    output_filename = "TrendWave_Short_Private.mp4"
    individual_scenes = []
    SPEED_FACTOR = 1.15
    
    # Anchor Overlay Graphic
    anchor_overlay = ColorClip(size=(W, 350), color=(0,0,0)).set_opacity(0.7).set_position(('center', 1570))
    anchor_text = TextClip("LIVE | TrendWave News", fontsize=45, color='white', font='Arial-Bold').set_position(('center', 'center'))

    for i, item in enumerate(items):
        tts_text = f"{item['type']}. {item['headline']}. {item['details']}"
        tts_file = f"voice_{i}.mp3"
        gTTS(text=tts_text, lang='en').save(tts_file)
        
        voice = AudioFileClip(tts_file)
        # We set the scene duration to the voice duration
        scene_dur = voice.duration

        bg_file = fetch_bg_image(item['search_key'], i)
        bg = ImageClip(bg_file).set_duration(scene_dur).resize(newsize=(W, H)) if bg_file else ColorClip(size=(W, H), color=(20, 20, 40), duration=scene_dur)
        
        h_clip = TextClip(item['headline'], fontsize=80, color='yellow', font='Arial-Bold', method='caption', size=(W-100, None)).set_duration(scene_dur).set_position(('center', 300))
        d_clip = TextClip(item['details'], fontsize=50, color='white', font='Arial', method='caption', size=(W-150, None)).set_start(0.5).set_duration(scene_dur-0.5).set_position(('center', 700))
        
        anchor_bar = CompositeVideoClip([anchor_overlay, anchor_text], size=(W, 350)).set_duration(scene_dur).set_position(('center', 1570))
        
        # Build normal speed scene
        scene = CompositeVideoClip([bg, h_clip, d_clip, anchor_bar]).set_audio(voice).set_duration(scene_dur)
        
        # Apply speed effect to individual scene to prevent cumulative math errors
        fast_scene = scene.fx(vfx.speedx, SPEED_FACTOR)
        individual_scenes.append(fast_scene)

    # Combine all fast scenes
    news_body = concatenate_videoclips(individual_scenes, method="compose")
    
    # Safety: Explicitly set duration to avoid "Accessing time t..." errors
    final_dur = news_body.duration - 0.1 
    news_body = news_body.subclip(0, final_dur)

    # Overlays
    p_sub = TextClip("Please subscribe TrendWave Now", fontsize=40, color='cyan', font='Arial-Bold').set_duration(final_dur).set_position(('center', 1800))
    l_cta = TextClip("Tune with us for more such news", fontsize=50, color='white', font='Arial-Bold', method='caption', size=(W-100, None)).set_start(max(0, final_dur - 2)).set_duration(2).set_position(('center', 1450))

    final_video = CompositeVideoClip([news_body, p_sub, l_cta])
    
    if os.path.exists("bg_music.mp3"):
        bg_music = AudioFileClip("bg_music.mp3").volumex(0.1).set_duration(final_dur)
        final_video.audio = CompositeAudioClip([final_video.audio, bg_music])

    # Render
    final_video.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", logger=None)
    
    # Cleanup
    final_video.close()
    for i in range(len(items)): 
        if os.path.exists(f"voice_{i}.mp3"):
            try: os.remove(f"voice_{i}.mp3")
            except: pass

    if input("\n🚀 Video fixed. Upload? (y/n): ").lower() == 'y':
        meta = {"video_name": output_filename, "day": "Feb 12, 2026", "location": "Global", "is_news": True, "description": "Breaking news bulletin. Tune with us for more such news."}
        with open("upload.json", "w") as f: json.dump(meta, f)
        subprocess.run(["python", "stage3_upload.py", "--json", "upload.json"])

if __name__ == "__main__":
    create_short(news_items)