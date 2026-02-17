import os, json, shutil, time, gc
from datetime import datetime
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from PIL import Image
from icrawler.builtin import BingImageCrawler

# --- IMPORT UPLOAD SCRIPT ---
try:
    from stage3_upload import upload_from_json
except ImportError:
    print("⚠️ stage3_upload.py not found. Upload will be skipped.")

# --- CONFIG ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})
W, H = 720, 1280 
BGM_PATH = "bg_music.mp3"
SPEED_FACTOR = 1.20  # Updated to 1.20x speed

def fetch_and_clean_images(query, index):
    raw_dir, clean_dir = f"raw_{index}", f"clean_{index}"
    for d in [raw_dir, clean_dir]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)
    main_term = query.split('|')[0].strip()
    crawler = BingImageCrawler(storage={'root_dir': raw_dir}, log_level=50)
    crawler.crawl(keyword=f"{main_term} cinematic 4k", max_num=5)
    valid_paths = []
    for f in sorted(os.listdir(raw_dir)):
        try:
            with Image.open(os.path.join(raw_dir, f)) as img:
                p = os.path.join(clean_dir, f"{f}.jpg")
                img.convert('RGB').save(p, "JPEG")
                valid_paths.append(p)
        except: continue
    return valid_paths

def generate_video(json_file):
    with open(json_file, "r", encoding="utf-8") as f: 
        items = json.load(f)

    for i, item in enumerate(items):
        v_title = item.get('metadata', {}).get('title', "Viral News")
        print(f"\n🎬 Processing Video {i+1} | {v_title}")
        
        # Audio generation
        q_path, a_path = f"q_{i}.mp3", f"a_{i}.mp3"
        gTTS(text=item['hook_text'], lang='en').save(q_path)
        gTTS(text=item['details'], lang='en').save(a_path)
        q_audio, a_audio = AudioFileClip(q_path), AudioFileClip(a_path)
        silence = AudioClip(lambda t: [0,0], duration=1.0, fps=44100)
        audio = concatenate_audioclips([q_audio, silence, a_audio])
        dur = audio.duration

        # 1. Subtitles
        sub_text = f"{item['hook_text']}\n\n{item['details']}"
        subtitles = TextClip(sub_text, fontsize=34, color='white', font='Arial-Bold',
                             stroke_color='black', stroke_width=1.5,
                             method='caption', size=(W-100, None), align='center').set_duration(dur).set_position(('center', 850))

        # 2. Red Background Subscribe Banner (Replaces old watermark)
        subscribe_banner = TextClip(" PLEASE SUBSCRIBE WITH US ", fontsize=32, color='white', 
                                    bg_color='red', font='Arial-Bold').set_duration(dur).set_position(('center', 20))

        # 3. Visuals
        header = TextClip(item['headline'], fontsize=48, color='yellow', font='Arial-Bold', 
                          size=(W-80, None), method='caption').set_duration(dur).set_position(('center', 80))
        
        img_paths = fetch_and_clean_images(item.get('search_key', ''), i)
        slides = [ImageClip(p).set_duration(dur/len(img_paths)).resize(height=550) for p in img_paths]
        slideshow = concatenate_videoclips(slides, method="compose").set_position(('center', 280))

        bg = ColorClip(size=(W, H), color=(0, 0, 15)).set_duration(dur)
        
        # CTA strictly in last scene
        cta = TextClip("Tune with us for more such news", fontsize=38, color='white', bg_color='darkred', 
                       size=(W, 100), method='caption').set_start(dur-3.5).set_duration(3.5).set_position(('center', H-180))

        # Compile and Apply Speed
        scene = CompositeVideoClip([bg, header, slideshow, subtitles, cta, subscribe_banner]).set_audio(audio)
        scene = scene.fx(vfx.speedx, SPEED_FACTOR)

        out_name = f"Short_{i+1}.mp4"
        scene.write_videofile(out_name, fps=24, codec="libx264")

        # --- 4. INVOKE PUBLISH ---
        try:
            print(f"📤 Uploading: {v_title}...")
            upload_from_json(json_file, video_file=out_name)
            print(f"✅ Upload Complete for {out_name}")
        except NameError:
            print("❌ Error: 'upload_from_json' not defined. Check your imports.")
        except Exception as e:
            print(f"⚠️ Upload failed for {out_name}: {e}")

        # Cleanup to save memory
        scene.close(); audio.close()
        if os.path.exists(q_path): os.remove(q_path)
        if os.path.exists(a_path): os.remove(a_path)
        gc.collect()

if __name__ == "__main__":
    generate_video("news_data.json")