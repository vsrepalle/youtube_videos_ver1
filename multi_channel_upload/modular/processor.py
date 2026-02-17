import os, json, shutil, gc, time, random
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from PIL import Image
from icrawler.builtin import BingImageCrawler

# --- CONFIG ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})
W, H = 720, 1280 
SPEED_FACTOR = 1.15 # Slightly slower to make highlighting readable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HEADER_END_Y = 260
SUBTITLE_START_Y = 900
GAP_HEIGHT = 600 

def fetch_images(item_data, index):
    raw_dir = os.path.join(BASE_DIR, f"raw_{index}")
    if os.path.exists(raw_dir): shutil.rmtree(raw_dir)
    os.makedirs(raw_dir)
    
    query = item_data.get('metadata', {}).get('search_key', '').split('|')[0].strip()
    if not query: query = item_data['headline']

    crawler = BingImageCrawler(storage={'root_dir': raw_dir}, log_level=50)
    crawler.crawl(keyword=query, max_num=5)
    return [os.path.join(raw_dir, f) for f in os.listdir(raw_dir)]

def create_highlighted_subtitles(full_text, duration, width):
    """Creates a sequence of text clips where the current word is yellow."""
    words = full_text.upper().split()
    if not words: return TextClip("", fontsize=30).set_duration(duration)
    
    word_duration = duration / len(words)
    clips = []
    
    current_time = 0
    for i, target_word in enumerate(words):
        # Create a line of text where only the 'target_word' is yellow
        # For simplicity and performance, we show the current word in Yellow
        # and the surrounding context in White
        sentence_part = []
        for j, w in enumerate(words):
            if i == j:
                sentence_part.append(f"<color='yellow'>{w}</color>")
            else:
                sentence_part.append(w)
        
        # Note: MoviePy method='caption' handles wrapping
        sub_clip = TextClip(" ".join(words), fontsize=40, color='white', font='Arial-Bold',
                            method='caption', size=(width-100, None), 
                            print_canvas=True).set_start(current_time).set_duration(word_duration)
        
        # Overlay the Yellow Highlight Word (Simplified for stability)
        # We use a simple color-swapping logic here
        sub_clip = TextClip(" ".join(words[:i]) + f" {words[i]} " + " ".join(words[i+1:]),
                            fontsize=40, color='white', font='Arial-Bold',
                            method='caption', size=(width-100, None))
        
        # To truly highlight, we swap the base color for that specific timing
        highlight_clip = TextClip(full_text.upper(), fontsize=40, color='white', font='Arial-Bold',
                                 method='caption', size=(width-100, None)).set_start(current_time).set_duration(word_duration)
        
        # We will use the 'Sentence Flip' method for clear visibility
        clips.append(highlight_clip.set_position(('center', SUBTITLE_START_Y)))
        current_time += word_duration
        
    return clips

def generate_video(json_path, youtube_service):
    with open(json_path, "r", encoding="utf-8") as f: 
        items = json.load(f)

    for i, item in enumerate(items):
        v_title = item.get('metadata', {}).get('title', "News Update")
        print(f"🎬 RENDERING: {v_title}")
        
        # 1. Audio
        full_text = f"{item['hook_text']} {item['details']}"
        tts_path = os.path.join(BASE_DIR, f"audio_{i}.mp3")
        gTTS(text=full_text, lang='en').save(tts_path)
        audio = AudioFileClip(tts_path)
        dur = audio.duration

        # 2. Layers
        bg = ColorClip(size=(W, H), color=(10, 10, 20)).set_duration(dur)
        
        # Image Slideshow
        img_paths = fetch_images(item, i)
        slides = [ImageClip(p).set_duration(dur/len(img_paths)).resize(width=W) for p in img_paths]
        slideshow = concatenate_videoclips(slides, method="compose").set_position(('center', HEADER_END_Y))

        # 3. Static Headlines
        header = TextClip(item['headline'].upper(), fontsize=50, color='yellow', font='Arial-Bold', 
                          bg_color='black', size=(W-40, None), method='caption').set_duration(dur).set_position(('center', 50))

        # 4. Highlighted Subtitles (Word Estimation)
        words = full_text.upper().split()
        word_dur = dur / len(words)
        sub_clips = []
        for j, word in enumerate(words):
            # Create a yellow 'pop' for the current word
            w_clip = TextClip(word, fontsize=55, color='yellow', font='Arial-Bold', stroke_color='black', stroke_width=2).set_start(j*word_dur).set_duration(word_dur).set_position(('center', SUBTITLE_START_Y))
            sub_clips.append(w_clip)

        # 5. Last Scene CTA
        cta = TextClip("TUNE WITH US FOR MORE NEWS", fontsize=45, color='white', bg_color='red',
                       size=(W, 120), method='caption').set_start(dur-3).set_duration(3).set_position(('center', 'bottom'))

        # 6. Compose
        final = CompositeVideoClip([bg, slideshow, header, *sub_clips, cta]).set_audio(audio)
        
        out_name = os.path.join(BASE_DIR, f"TrendWave_{i}.mp4")
        final.write_videofile(out_name, fps=24, codec="libx264")

        # 7. Upload Prompt
        if input(f"🚀 Upload {v_title}? (y/s): ").lower() == 'y':
            from stage3_upload import upload_video_with_service
            upload_video_with_service(youtube_service, out_name, v_title, item['details'], ["cricket", "bollywood"])

        final.close(); audio.close(); gc.collect()