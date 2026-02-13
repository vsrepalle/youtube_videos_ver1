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
BGM_PATH = "bg_music.mp3"

# --- LAYOUT CONSTANTS (NO OVERLAP) ---
HEADER_Y = 60
IMAGE_ZONE_Y = 250
IMAGE_ZONE_H = 600
TICKER_H = 240

# --- INTERNAL FUNCTIONS ---

def create_synced_subtitles(full_text, duration):
    """Syncs text segments based on character length relative to audio duration."""
    sentences = [s.strip() for s in full_text.replace('!', '.').replace('?', '.').split('.') if len(s.strip()) > 5]
    total_chars = sum(len(s) for s in sentences)
    
    news_bar = ColorClip(size=(W, TICKER_H), color=(180, 0, 0)).set_duration(duration).set_position(('center', H - TICKER_H))
    
    def make_progress_bar(t):
        current_w = max(1, int(W * (t / duration)))
        return ColorClip(size=(current_w, 10), color=(255, 255, 255)).get_frame(t)
    prog_bar = VideoClip(make_progress_bar, duration=duration).set_position((0, H - TICKER_H))

    clips = [news_bar, prog_bar]
    current_time = 0
    
    for s in sentences:
        s_dur = (len(s) / total_chars) * duration
        txt = TextClip(s, fontsize=32, color='white', font='Arial-Bold', method='caption', 
                       size=(W-100, TICKER_H-60), align='center'
                       ).set_start(current_time).set_duration(s_dur).set_position(('center', H - TICKER_H + 30))
        clips.append(txt)
        current_time += s_dur
        
    return clips

def fetch_images_extended(query, index):
    """Fetches up to 10 images for smooth 5-second rotations."""
    save_dir = f"temp_imgs_{index}"
    if os.path.exists(save_dir): shutil.rmtree(save_dir)
    os.makedirs(save_dir)
    
    crawler = BingImageCrawler(storage={'root_dir': save_dir}, log_level=50)
    search_term = query.split('|')[0].strip()
    crawler.crawl(keyword=f"{search_term} high resolution", max_num=10)
    
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
        print(f"❌ {json_file} not found.")
        return

    with open(json_file, "r", encoding="utf-8") as f: 
        items = json.load(f)

    scenes = []
    for i, item in enumerate(items):
        print(f"🎬 Creating Scene {i+1} of {len(items)}...")
        
        tts_text = f"{item['hook_text']}. {item['headline']}. {item['details']}"
        voice_file = f"voice_{i}.mp3"
        gTTS(text=tts_text, lang='en').save(voice_file)
        voice = AudioFileClip(voice_file)
        dur = voice.duration

        header = TextClip(item['hook_text'].upper(), fontsize=38, color='yellow', font='Arial-Bold',
                          method='caption', size=(W-80, 150), align='center'
                          ).set_duration(dur).set_position(('center', HEADER_Y))

        # --- FIX FOR BLUE SCREEN: ADDED .loop(duration=dur) ---
        img_paths = fetch_images_extended(item.get('search_key', ''), i)
        if img_paths:
            img_clips = [ImageClip(p).set_duration(5).resize(height=IMAGE_ZONE_H) for p in img_paths]
            # Looping ensures that if voice is 20s and we only have 2 images (10s total), they repeat.
            img_slideshow = concatenate_videoclips(img_clips, method="compose").loop(duration=dur).set_position(('center', IMAGE_ZONE_Y))
        else:
            # Absolute fallback if zero images are found
            img_slideshow = ColorClip(size=(W-60, IMAGE_ZONE_H), color=(30,30,40)).set_duration(dur).set_position(('center', IMAGE_ZONE_Y))

        border = ColorClip(size=(W-40, IMAGE_ZONE_H+10), color=(0, 100, 255)).set_duration(dur).set_position(('center', IMAGE_ZONE_Y-5))
        footer_layers = create_synced_subtitles(item['details'], dur)

        canvas = ColorClip(size=(W, H), color=(5, 5, 10)).set_duration(dur)

        scene = CompositeVideoClip([canvas, header, border, img_slideshow] + footer_layers, size=(W, H)).set_audio(voice)
        scenes.append(scene)

    if not scenes: return
    
    final_video = concatenate_videoclips(scenes, method="chain")

    cta = TextClip("Tune with us for more news", fontsize=36, color='white', bg_color='darkred',
                   method='caption', size=(W, 120), align='center'
                   ).set_start(final_video.duration - 4).set_duration(4).set_position(('center', H-420))
    
    final_comp = CompositeVideoClip([final_video, cta])

    if os.path.exists(BGM_PATH):
        bgm = AudioFileClip(BGM_PATH).volumex(0.12).set_duration(final_comp.duration)
        final_comp = final_comp.set_audio(CompositeAudioClip([final_comp.audio, bgm]))

    output_name = f"News_Final_{datetime.now().strftime('%H%M')}.mp4"
    print(f"🚀 Rendering optimized MP4...")
    final_comp.write_videofile(output_name, fps=24, codec="libx264", audio_codec="aac", threads=8, logger='bar')

    choice = input(f"\nUpload {output_name} as Private? (y/n): ").lower().strip()
    if choice in ['y', 'yes']:
        from stage3_upload import upload_from_json
        upload_from_json(json_file, video_file=output_name)

if __name__ == "__main__":
    generate_video_and_upload("news_data.json")