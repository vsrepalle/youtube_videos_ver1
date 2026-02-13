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

W, H = 720, 1280 # Optimized for Speed

# --- INTERNAL FUNCTIONS (Replacing video_effects.py) ---

def apply_ken_burns(clip, zoom_ratio=0.04):
    """Smooth zoom effect."""
    return clip.fx(vfx.resize, lambda t: 1.0 + (zoom_ratio * t))

def create_news_ticker_with_subtitles(full_text, duration):
    """Creates a Red Breaking News bar with white scrolling text."""
    sentences = full_text.replace('!', '.').replace('?', '.').split('.')
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    
    # Red Bar at the bottom
    news_bar = ColorClip(size=(W, 250), color=(200, 0, 0)).set_duration(duration).set_position(('center', H-250))
    
    if not sentences:
        return news_bar

    each_dur = duration / len(sentences)
    text_clips = []
    
    for i, sentence in enumerate(sentences):
        txt = TextClip(sentence, fontsize=42, color='white', font='Arial-Bold',
                       method='caption', size=(W-80, 200), align='center'
                       ).set_duration(each_dur).set_start(i * each_dur).set_position(('center', H-220))
        text_clips.append(txt)
        
    return CompositeVideoClip([news_bar] + text_clips, size=(W, H))

def fetch_and_prepare_images(query, index):
    """Downloads images and forces RGB mode to prevent 'Broadcast' errors."""
    save_dir = f"temp_imgs_{index}"
    if os.path.exists(save_dir): shutil.rmtree(save_dir)
    os.makedirs(save_dir)
    
    crawler = BingImageCrawler(storage={'root_dir': save_dir}, log_level=50)
    crawler.crawl(keyword=f"{query} cricket match highlights", max_num=3)
    
    valid_paths = []
    for f in os.listdir(save_dir):
        p = os.path.join(save_dir, f)
        try:
            with Image.open(p) as img:
                img.convert('RGB').save(p)
                valid_paths.append(p)
        except: continue
    return valid_paths

# --- MAIN GENERATOR ---

def generate_video_and_upload(json_file):
    if not os.path.exists(json_file):
        print(f"❌ Error: {json_file} not found.")
        return
    
    output_video = f"Breaking_News_{datetime.now().strftime('%H%M')}.mp4"
    with open(json_file, "r", encoding="utf-8") as f: 
        items = json.load(f)

    scenes = []
    for i, item in enumerate(items):
        print(f"🎬 Processing News Item {i+1}...")
        
        # 1. Voiceover
        tts_text = f"{item['hook_text']}. {item['headline']}. {item['details']}"
        tts_file = f"voice_{i}.mp3"
        gTTS(text=tts_text, lang='en').save(tts_file)
        voice = AudioFileClip(tts_file)
        dur = voice.duration

        # 2. Background (Image + Ken Burns)
        search_key = item.get('search_key', '').split('|')[0].strip()
        images = fetch_and_prepare_images(search_key, i)
        
        if images:
            img_clips = [ImageClip(p).set_duration(dur/len(images)).resize(height=H).set_position('center') for p in images]
            bg = concatenate_videoclips(img_clips, method="chain")
        else:
            bg = ColorClip(size=(W, H), color=(15, 15, 30)).set_duration(dur)
        
        bg = apply_ken_burns(bg)

        # 3. Header Text
        header = TextClip(item['hook_text'].upper(), fontsize=70, color='yellow', font='Arial-Bold',
                          method='caption', size=(W-60, None), bg_color='black').set_duration(dur).set_position(('center', 150))

        # 4. News Ticker Footer
        footer = create_news_ticker_with_subtitles(item['details'], dur)

        # Combine Scene
        scene = CompositeVideoClip([bg, header, footer], size=(W, H)).set_audio(voice)
        scenes.append(scene)

    # Final Video Construction
    final = concatenate_videoclips(scenes, method="chain")
    
    # CTA - Strictly in the last scene (per instructions)
    cta = TextClip("Tune with us for more news", fontsize=40, color='white', font='Arial-Bold', 
                   bg_color='black').set_start(final.duration - 3.5).set_duration(3.5).set_position(('center', H-400))
    
    final_video = CompositeVideoClip([final, cta])

    # Rendering with Progress Bar
    print(f"🚀 Rendering optimized MP4...")
    final_video.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac", 
                                threads=8, preset="ultrafast", logger='bar')
    
    # Upload Logic
    choice = input(f"\nUpload {output_video} to YouTube as Private? (yes/no): ").lower().strip()
    if choice == 'yes':
        from stage3_upload import upload_from_json
        upload_from_json(json_file, video_file=output_video)

if __name__ == "__main__":
    generate_video_and_upload("news_data.json")