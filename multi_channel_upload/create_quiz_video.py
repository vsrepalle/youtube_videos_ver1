import os, json, random, shutil
from datetime import datetime
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from PIL import Image, ImageFilter
from icrawler.builtin import BingImageCrawler
from visual_effects import get_styled_header, get_progress_bar

# --- CONFIG ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

W, H = 720, 1280 
SPEED_FACTOR = 1.1 

def get_static_answer_box(text, dur, W, box_h):
    """Creates a static, multi-line text box instead of a scrolling ticker."""
    from visual_effects import create_rounded_box
    box_w = W - 60
    bg = create_rounded_box(box_w, box_h, (120, 0, 0), opacity=255) # Deep red
    
    # Use 'caption' instead of 'label' to wrap text and keep it static
    txt = TextClip(text, fontsize=34, color='white', font='Arial-Bold', 
                   size=(box_w-40, box_h-20), method='caption', align='center').set_duration(dur)
    
    return CompositeVideoClip([bg, txt.set_position('center')], size=(box_w, box_h)).set_duration(dur)

def fetch_quiz_bg(query, index):
    raw_dir = f"quiz_raw_{index}"
    if os.path.exists(raw_dir): shutil.rmtree(raw_dir)
    os.makedirs(raw_dir)
    search_term = query.split('|')[0].strip()
    crawler = BingImageCrawler(storage={'root_dir': raw_dir}, log_level=50)
    crawler.crawl(keyword=f"{search_term} 4k space background", max_num=1)
    
    files = os.listdir(raw_dir)
    if not files: return ColorClip(size=(W, H), color=(10, 15, 35))
    
    processed_path = f"quiz_bg_{index}.jpg"
    with Image.open(os.path.join(raw_dir, files[0])) as img:
        img = img.convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
        img = img.filter(ImageFilter.GaussianBlur(radius=15))
        img.save(processed_path)
    
    return CompositeVideoClip([ImageClip(processed_path), ColorClip(size=(W, H), color=(0, 0, 0)).set_opacity(0.5)])

def generate_quiz_video(json_file):
    if not os.path.exists(json_file): return None
    with open(json_file, "r", encoding="utf-8") as f: items = json.load(f)

    all_scenes = []
    for i, item in enumerate(items):
        print(f"🎬 Processing: {item['headline']}")
        
        # 1. AUDIO (Strictly single generation)
        q_path, a_path = f"q_{i}.mp3", f"a_{i}.mp3"
        gTTS(text=item['hook_text'], lang='en').save(q_path)
        # Note: We only say "The answer is" once
        gTTS(text=f"The answer is {item['details']}", lang='en').save(a_path)
        
        q_audio = AudioFileClip(q_path)
        a_audio = AudioFileClip(a_path)
        silence_gap = AudioClip(lambda t: [0, 0], duration=1.5, fps=44100)
        
        full_audio = concatenate_audioclips([q_audio, silence_gap, a_audio])
        dur = full_audio.duration

        # 2. VISUALS
        bg = fetch_quiz_bg(item.get('search_key', 'Quiz'), i).set_duration(dur)
        header = get_styled_header(item['headline'], dur, W).set_position(('center', 80))
        
        # Center Question (Static)
        question_display = TextClip(item['hook_text'], fontsize=48, color='white', font='Arial-Bold',
                                    size=(W-100, 450), method='caption', align='center').set_duration(dur).set_position('center')

        # NEW: Static Answer Box (Replaces Ticker)
        footer = get_static_answer_box(item['details'], dur, W, 280).set_position(('center', 960))
        
        prog_bar = get_progress_bar(dur, W, H)

        # 3. ASSEMBLE
        scene = CompositeVideoClip([bg, header, question_display, footer, prog_bar])
        scene = scene.set_audio(full_audio).fx(vfx.speedx, SPEED_FACTOR)
        all_scenes.append(scene)

    if not all_scenes: return None

    final_v = concatenate_videoclips(all_scenes, method="compose")
    
    # CTA logic
    cta = TextClip("Tune with us for more such news", fontsize=40, color='yellow', bg_color='black', 
                   size=(W, 120), method='caption').set_start(final_v.duration-3.5).set_duration(3.5).set_position(('center', H-450))
    
    final_video = CompositeVideoClip([final_v, cta])
    out_name = f"Quiz_{datetime.now().strftime('%M%S')}.mp4"
    final_video.write_videofile(out_name, fps=24, codec="libx264")
    
    # Cleanup temp files
    shutil.rmtree(f"quiz_raw_{i}", ignore_errors=True)
    return out_name