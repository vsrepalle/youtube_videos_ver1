import os, json, shutil, gc, time
import tkinter as tk
from tkinter import filedialog
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from PIL import Image
from icrawler.builtin import BingImageCrawler

# --- IMPORT UPLOAD LOGIC ---
try: 
    from stage3_upload import get_authenticated_service, upload_from_json
except ImportError: 
    print("⚠️ stage3_upload.py not found.")

# --- CONFIG ---
# Ensure this path matches your ImageMagick installation
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})
W, H = 720, 1280 
SPEED_FACTOR = 1.20

# UI Dimensions for Ken Burns Gap
HEADER_END_Y = 260
SUBTITLE_START_Y = 880
GAP_HEIGHT = SUBTITLE_START_Y - HEADER_END_Y 

def fetch_and_clean_images(query, index):
    raw_dir, clean_dir = f"raw_{index}", f"clean_{index}"
    for d in [raw_dir, clean_dir]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)
    
    # Use preference format: Vijay Jana Nayagan | Bobby Deol Jana Nayagan
    main_term = query.split('|')[0].strip()
    crawler = BingImageCrawler(storage={'root_dir': raw_dir}, log_level=50)
    crawler.crawl(keyword=f"{main_term} cinematic 4k", max_num=4)
    
    valid_paths = []
    # FIX: Splitting extension to avoid .jpg.jpg bug
    for i, f in enumerate(os.listdir(raw_dir)):
        raw_path = os.path.join(raw_dir, f)
        if not os.path.isfile(raw_path): continue
        
        try:
            with Image.open(raw_path) as img:
                # Get filename without extension
                clean_name = f"image_{i}.jpg" 
                p = os.path.join(clean_dir, clean_name)
                img.convert('RGB').save(p, "JPEG")
                valid_paths.append(p)
        except Exception as e:
            print(f"Skipping bad image {f}: {e}")
            
    return valid_paths

def apply_ken_burns(clip):
    """Cinematic slow zoom-in effect (100% to 110%)."""
    return clip.fx(vfx.resize, lambda t: 1 + 0.04 * t) 

def generate_video(json_path):
    with open(json_path, "r", encoding="utf-8") as f: 
        items = json.load(f)

    for i, item in enumerate(items):
        v_title = item.get('metadata', {}).get('title', "News Update")
        print(f"\n🎬 Rendering {i+1}/{len(items)} | {v_title} (Ken Burns Mode)")
        
        # 1. Audio Generation
        full_text = f"{item['hook_text']} {item['details']}"
        tts_path = f"audio_{i}.mp3"
        gTTS(text=full_text, lang='en').save(tts_path)
        audio = AudioFileClip(tts_path)
        dur = audio.duration

        # 2. UI Layers
        bg = ColorClip(size=(W, H), color=(0, 0, 20)).set_duration(dur)
        banner = TextClip(" PLEASE SUBSCRIBE WITH US ", fontsize=32, color='white', 
                          bg_color='red', font='Arial-Bold').set_duration(dur).set_position(('center', 20))
        header = TextClip(item['headline'], fontsize=48, color='yellow', font='Arial-Bold', 
                          size=(W-80, 180), method='caption').set_duration(dur).set_position(('center', 100))

        # 3. Dynamic Visuals (Ken Burns + Fill Gap)
        img_paths = fetch_and_clean_images(item.get('search_key', ''), i)
        if not img_paths:
            slideshow = ColorClip(size=(W, GAP_HEIGHT), color=(30, 30, 30)).set_duration(dur).set_position(('center', HEADER_END_Y))
        else:
            slide_dur = dur / len(img_paths)
            slides = []
            for p in img_paths:
                # Resize and zoom to fill the large visual gap
                img_clip = ImageClip(p).set_duration(slide_dur).resize(width=W).resize(height=GAP_HEIGHT)
                img_clip = apply_ken_burns(img_clip)
                slides.append(img_clip)
            slideshow = concatenate_videoclips(slides, method="compose").set_position(('center', HEADER_END_Y))

        # 4. Sentence Subtitles
        sent_dur = dur / 2
        s1 = TextClip(item['hook_text'].upper(), fontsize=36, color='white', method='caption', 
                      size=(W-100, None)).set_duration(sent_dur).set_position(('center', SUBTITLE_START_Y))
        s2 = TextClip(item['details'].upper(), fontsize=36, color='yellow', method='caption', 
                      size=(W-100, None)).set_start(sent_dur).set_duration(sent_dur).set_position(('center', SUBTITLE_START_Y))

        # 5. Last Scene CTA (Strict Constraint)
        cta = TextClip("Tune with us for more such news", fontsize=38, color='white', bg_color='darkred', 
                       size=(W, 100), method='caption').set_start(dur-3.5).set_duration(3.5).set_position(('center', H-150))

        # 6. Assemble + Speed Optimization
        final = CompositeVideoClip([bg, header, banner, slideshow, s1, s2, cta]).set_audio(audio)
        final = final.fx(vfx.speedx, SPEED_FACTOR)

        out_name = f"Short_{i+1}.mp4"
        final.write_videofile(out_name, fps=24, codec="libx264", threads=8, preset="ultrafast")
        
        # 7. Release & Auto-Upload (Private by Default)
        final.close(); audio.close()
        time.sleep(1)
        try:
            upload_from_json(json_path, video_file=out_name, index=i)
        except Exception as e:
            print(f"⚠️ Upload invocation skipped: {e}")

        gc.collect()

if __name__ == "__main__":
    # Windows Explorer JSON Picker
    root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
    selected_json = filedialog.askopenfilename(title="Select Metadata JSON", filetypes=[("JSON Files", "*.json")])
    root.destroy()
    
    if selected_json:
        generate_video(selected_json)
    else:
        print("🛑 Error: No JSON file selected.")