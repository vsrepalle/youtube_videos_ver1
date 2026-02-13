import os, json, shutil, time
from datetime import datetime
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from PIL import Image
from icrawler.builtin import BingImageCrawler
import moviepy.video.fx.all as vfx

# --- CONFIGURATION ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

W, H = 720, 1280 

# --- INTERNAL LOGIC (Replacing video_effects.py) ---

def apply_ken_burns_internal(clip, zoom_ratio=0.04):
    """Adds a smooth zoom-in effect to an image clip."""
    return clip.fx(vfx.resize, lambda t: 1.0 + (zoom_ratio * t))

def create_sentence_scrolling_internal(full_text, duration):
    """Creates a news bar with scrolling subtitles."""
    sentences = full_text.replace('!', '.').replace('?', '.').split('.')
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    
    # The Red Breaking News Bar
    news_bar = ColorClip(size=(W, 250), color=(200, 0, 0)).set_duration(duration).set_position(('center', H-250))
    
    if not sentences:
        return news_bar

    each_dur = duration / len(sentences)
    text_clips = []
    
    for i, sentence in enumerate(sentences):
        txt = TextClip(sentence, fontsize=45, color='white', font='Arial-Bold',
                       method='caption', size=(W-60, 200), align='center'
                       ).set_duration(each_dur).set_start(i * each_dur).set_position(('center', H-225))
        text_clips.append(txt)
        
    return CompositeVideoClip([news_bar] + text_clips, size=(W, H))

def fetch_and_fix_images(query, index):
    """Downloads images and ensures they are RGB to prevent render crashes."""
    save_dir = f"downloads_{index}"
    if os.path.exists(save_dir): shutil.rmtree(save_dir)
    os.makedirs(save_dir)
    
    crawler = BingImageCrawler(storage={'root_dir': save_dir}, log_level=50)
    crawler.crawl(keyword=f"{query} cricket stadium action", max_num=3)
    
    valid_paths = []
    for f in os.listdir(save_dir):
        p = os.path.join(save_dir, f)
        try:
            with Image.open(p) as img:
                img.convert('RGB').save(p) # Force RGB
                valid_paths.append(p)
        except: continue
    return valid_paths

# --- MAIN ENGINE ---

def generate_video_and_upload(json_file):
    if not os.path.exists(json_file): return
    
    output_video = f"Breaking_News_{datetime.now().strftime('%H%M')}.mp4"
    with open(json_file, "r", encoding="utf-8") as f: 
        items = json.load(f)

    scenes = []
    for i, item in enumerate(items):
        print(f"🎬 Building Scene {i+1}...")
        
        # 1. Voice
        tts_text = f"{item['hook_text']}. {item['headline']}. {item['details']}"
        tts_file = f"voice_{i}.mp3"
        gTTS(text=tts_text, lang='en').save(tts_file)
        voice = AudioFileClip(tts_file)
        dur = voice.duration

        # 2. Background
        search_key = item.get('search_key', '').split('|')[0].strip()
        images = fetch_and_fix_images(search_key, i)
        
        if images:
            img_clips = [ImageClip(p).set_duration(dur/len(images)).resize(height=H) for p in images]
            bg = concatenate_videoclips(img_clips, method="chain")
        else:
            bg = ColorClip(size=(W, H), color=(20, 20, 40)).set_duration(dur)
        
        bg = apply_ken_burns_internal(bg)

        # 3. Header (Hook)
        hook = TextClip(item['hook_text'].upper(), fontsize=75, color='yellow', font='Arial-Bold',
                        method='caption', size=(W-60, None), bg_color='black').set_duration(dur).set_position(('center', 150))

        # 4. Footer (News Bar)
        footer = create_sentence_scrolling_internal(item['details'], dur)

        scene = CompositeVideoClip([bg, hook, footer], size=(W, H)).set_audio(voice)
        scenes.append(scene)

    # Final Composite
    final = concatenate_videoclips(scenes, method="chain")
    
    # CTA (Only in last scene)
    cta = TextClip("Tune with us for more news", fontsize(40), color='white', font='Arial-Bold', 
                   bg_color='black').set_start(final.duration - 3).set_duration(3).set_position(('center', H-400))
    
    final_video = CompositeVideoClip([final, cta])

    print(f"🚀 Rendering at 720p...")
    final_video.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac", logger='bar')
    
    # Manual Upload Prompt
    choice = input(f"Upload {output_video} to YouTube? (yes/no): ").lower()
    if choice == 'yes':
        from stage3_upload import upload_from_json
        upload_from_json(json_file, video_file=output_video)

if __name__ == "__main__":
    generate_video_and_upload("news_data.json")