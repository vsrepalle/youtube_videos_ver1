import os, json, shutil, gc
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from PIL import Image
from icrawler.builtin import BingImageCrawler

# --- CONFIG ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})
W, H = 720, 1280 
SPEED_FACTOR = 1.20

# Optimized Dimensions
HEADER_H = 160
SUB_Y = 880 # Fixed position for subtitles

def fetch_and_clean_images(query, index):
    raw_dir, clean_dir = f"raw_{index}", f"clean_{index}"
    for d in [raw_dir, clean_dir]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)
    main_term = query.split('|')[0].strip()
    crawler = BingImageCrawler(storage={'root_dir': raw_dir}, log_level=50)
    crawler.crawl(keyword=f"{main_term} cinematic 4k", max_num=4) # Reduced to 4 images for speed
    return [os.path.join(clean_dir, f) for f in os.listdir(raw_dir)] # Simplified pathing

def generate_video(json_file):
    with open(json_file, "r", encoding="utf-8") as f: 
        items = json.load(f)

    for i, item in enumerate(items):
        print(f"\n🚀 Fast Rendering Video {i+1}...")
        
        # 1. Faster Audio Generation
        full_script = f"{item['hook_text']} {item['details']}"
        tts_path = f"t_{i}.mp3"
        gTTS(text=full_script, lang='en').save(tts_path)
        audio = AudioFileClip(tts_path)
        dur = audio.duration

        # 2. Optimized Subtitles (Grouped by sentence to reduce clip count)
        sentences = [item['hook_text'], item['details']]
        sent_dur = dur / len(sentences)
        sub_clips = []
        
        for idx, sent in enumerate(sentences):
            # Create ONE sentence clip instead of 50 word clips
            s_clip = TextClip(sent.upper(), fontsize=36, color='yellow', font='Arial-Bold',
                              method='caption', size=(W-100, None), stroke_color='black', stroke_width=1)
            s_clip = s_clip.set_start(idx * sent_dur).set_duration(sent_dur).set_position(('center', SUB_Y))
            sub_clips.append(s_clip)

        # 3. Dynamic Image Filling
        img_paths = fetch_and_clean_images(item.get('search_key', ''), i)
        # Image height covers the gap between Header and Subtitles
        img_h = SUB_Y - (HEADER_H + 40)
        slides = [ImageClip(p).set_duration(dur/len(img_paths)).resize(height=img_h) for p in img_paths]
        slideshow = concatenate_videoclips(slides, method="chain").set_position(('center', HEADER_H + 20))

        # 4. Static UI Elements
        header = TextClip(item['headline'], fontsize=48, color='yellow', bg_color='black',
                          size=(W-40, HEADER_H), method='caption').set_duration(dur).set_position(('center', 40))
        
        banner = TextClip(" PLEASE SUBSCRIBE WITH US ", fontsize=30, color='white', 
                          bg_color='red', font='Arial-Bold').set_duration(dur).set_position(('center', 10))

        cta = TextClip("Tune with us for more such news", fontsize=34, color='white', bg_color='darkred', 
                       size=(W, 100), method='caption').set_start(dur-3.0).set_duration(3.0).set_position(('center', H-120))

        # 5. Final Composition (Flattened for speed)
        bg = ColorClip(size=(W, H), color=(0, 0, 20)).set_duration(dur)
        final = CompositeVideoClip([bg, header, banner, slideshow, cta] + sub_clips).set_audio(audio)
        
        # Apply 1.2x Speed
        final = final.fx(vfx.speedx, SPEED_FACTOR)

        # FAST WRITE: Using threads and a faster preset
        final.write_videofile(f"Fast_Short_{i+1}.mp4", fps=24, codec="libx264", 
                             threads=8, preset="ultrafast", logger=None)

        # Cleanup
        audio.close(); final.close()
        if os.path.exists(tts_path): os.remove(tts_path)
        gc.collect()

if __name__ == "__main__":
    generate_video("news_data.json")