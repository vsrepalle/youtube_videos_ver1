import os, json, shutil, time
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
    print("⚠️ stage3_upload.py not found. Please ensure it is in the same directory.")

# --- CONFIG ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})
W, H = 720, 1280 
BGM_PATH = "bg_music.mp3"
SPEED_FACTOR = 1.1

def get_static_footer_box(text, dur, W, box_h):
    from visual_effects import create_rounded_box
    box_w = W - 60
    bg = create_rounded_box(box_w, box_h, (0, 20, 60), opacity=230) 
    txt = TextClip(text, fontsize=32, color='white', font='Arial-Bold', 
                   size=(box_w-40, box_h-20), method='caption', align='center').set_duration(dur)
    return CompositeVideoClip([bg, txt.set_position('center')], size=(box_w, box_h)).set_duration(dur)

def fetch_and_clean_images(query, index):
    raw_dir, clean_dir = f"raw_{index}", f"clean_{index}"
    for d in [raw_dir, clean_dir]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)
    main_term = query.split('|')[0].strip()
    crawler = BingImageCrawler(storage={'root_dir': raw_dir}, log_level=50)
    crawler.crawl(keyword=f"{main_term} cinematic space 4k", max_num=5)
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
    with open(json_file, "r", encoding="utf-8") as f: items = json.load(f)

    for i, item in enumerate(items):
        chan_id = item.get('channel_id', 'YourChannel')
        print(f"\n🚀 Creating Video {i+1} of {len(items)}: {item['headline']}")
        
        # Audio
        q_path, a_path = f"q_{i}.mp3", f"a_{i}.mp3"
        gTTS(text=item['hook_text'], lang='en').save(q_path)
        gTTS(text=item['details'], lang='en').save(a_path)
        q_audio, a_audio = AudioFileClip(q_path), AudioFileClip(a_path)
        silence = AudioClip(lambda t: [0, 0], duration=1.5, fps=44100)
        audio = concatenate_audioclips([q_audio, silence, a_audio])
        dur = audio.duration

        # Watermark
        watermark = TextClip(f"Subscribe: @{chan_id}", fontsize=24, color='white', 
                             font='Arial-Bold', method='label').set_duration(dur).set_opacity(0.6).set_position(('right', 20))

        # Visuals
        header = TextClip(item['headline'], fontsize=50, color='yellow', font='Arial-Bold').set_duration(dur).set_position(('center', 60))
        footer = get_static_footer_box(item['details'], dur, W, 320).set_position(('center', 900))
        
        img_paths = fetch_and_clean_images(item.get('search_key', ''), i)
        slides = [ImageClip(p).set_duration(dur/len(img_paths)).resize(height=520) for p in img_paths]
        slideshow = concatenate_videoclips(slides, method="compose").set_position(('center', 320))

        bg = ColorClip(size=(W, H), color=(0, 0, 10)).set_duration(dur)
        cta = TextClip("Tune with us for more such news", fontsize=38, color='white', bg_color='darkred', 
                       size=(W, 100), method='caption').set_start(dur-3.5).set_duration(3.5).set_position(('center', H-220))

        scene = CompositeVideoClip([bg, header, slideshow, footer, cta, watermark]).set_audio(audio)
        scene = scene.fx(vfx.speedx, SPEED_FACTOR)

        out_name = f"Output_{i+1}.mp4"
        scene.write_videofile(out_name, fps=24, codec="libx264")
        print(f"✅ Saved: {out_name}")

        # --- INVOKING UPLOAD ---
        try:
            print(f"📤 Starting private upload for {out_name}...")
            upload_from_json(json_file, video_file=out_name)
            print("🚀 Upload complete!")
        except Exception as e:
            print(f"❌ Upload failed: {e}")

if __name__ == "__main__":
    generate_video("news_data.json")