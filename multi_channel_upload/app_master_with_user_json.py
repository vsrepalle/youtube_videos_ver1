import os, json, shutil, time, gc
from datetime import datetime
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

# UI Dimensions for Dynamic Scaling
HEADER_H = 180
BANNER_H = 60
SUBTITLE_H = 250
CTA_H = 120
# Image Height = Total - (Header + Subtitles + CTA + Spacing)
IMAGE_H = H - (HEADER_H + SUBTITLE_H + CTA_H + 100) 

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

def create_highlighted_subs(full_text, duration):
    """Creates a word-by-word highlighting effect."""
    words = full_text.split()
    word_dur = duration / len(words)
    clips = []
    
    for idx, word in enumerate(words):
        start_t = idx * word_dur
        # The 'base' sentence in dim white
        base = TextClip(full_text, fontsize=38, color='gray', font='Arial-Bold',
                        method='caption', size=(W-100, SUBTITLE_H), align='center').set_duration(word_dur).set_start(start_t)
        
        # We find the position of the word to highlight (Simplified for this version)
        # For a true highlight, we overlay the active word in Yellow/Cyan
        # Here we just show the sentence with the active word colored
        highlighted_sentence = full_text.replace(word, f"<font color='yellow'>{word}</font>")
        
        # Note: Standard TextClip doesn't support HTML. 
        # We'll use a cleaner approach: Show the word being spoken prominently.
        active_word_clip = TextClip(word.upper(), fontsize=55, color='yellow', font='Arial-Bold',
                                    stroke_color='black', stroke_width=2).set_duration(word_dur).set_start(start_t).set_position(('center', 950))
        
        clips.append(active_word_clip)
    
    return clips

def generate_video(json_file):
    with open(json_file, "r", encoding="utf-8") as f: 
        items = json.load(f)

    for i, item in enumerate(items):
        v_title = item.get('metadata', {}).get('title', "Viral News")
        print(f"\n🎬 Rendering with Word Highlights | {v_title}")
        
        # Audio
        full_script = f"{item['hook_text']} {item['details']}"
        tts_path = f"audio_{i}.mp3"
        gTTS(text=full_script, lang='en').save(tts_path)
        audio = AudioFileClip(tts_path)
        dur = audio.duration

        # 1. UI Components
        bg = ColorClip(size=(W, H), color=(10, 10, 30)).set_duration(dur)
        
        sub_banner = TextClip(" PLEASE SUBSCRIBE WITH US ", fontsize=32, color='white', 
                              bg_color='red', font='Arial-Bold').set_duration(dur).set_position(('center', 20))

        header = TextClip(item['headline'], fontsize=50, color='yellow', font='Arial-Bold', 
                          size=(W-80, HEADER_H), method='caption').set_duration(dur).set_position(('center', 100))

        # 2. DYNAMIC IMAGE SCALING
        img_paths = fetch_and_clean_images(item.get('search_key', ''), i)
        # Image height is now calculated to fill the gap perfectly
        slides = [ImageClip(p).set_duration(dur/len(img_paths)).resize(height=IMAGE_H) for p in img_paths]
        slideshow = concatenate_videoclips(slides, method="compose").set_position(('center', 300))

        # 3. WORD HIGHLIGHTING
        word_clips = create_highlighted_subs(full_script, dur)

        # 4. CTA
        cta = TextClip("Tune with us for more such news", fontsize=38, color='white', bg_color='darkred', 
                       size=(W, CTA_H), method='caption').set_start(dur-3.5).set_duration(3.5).set_position(('center', H-150))

        # Compile
        final_video = CompositeVideoClip([bg, header, slideshow, sub_banner, cta] + word_clips).set_audio(audio)
        final_video = final_video.fx(vfx.speedx, SPEED_FACTOR)

        out_name = f"Short_Pro_{i+1}.mp4"
        final_video.write_videofile(out_name, fps=24, codec="libx264")
        
        # Cleanup
        audio.close()
        if os.path.exists(tts_path): os.remove(tts_path)
        gc.collect()

if __name__ == "__main__":
    generate_video("news_data.json")