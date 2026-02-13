import os, json, shutil, time, sys
from datetime import datetime
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from PIL import Image
from icrawler.builtin import BingImageCrawler

# --- CONFIGURATION ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

W, H = 720, 1280 
BGM_PATH = "bg_music.mp3"
HEADER_Y, IMAGE_ZONE_Y, IMAGE_ZONE_H, TICKER_H = 60, 250, 600, 240

def log(msg, level="INFO"):
    colors = {"INFO": "🔵", "WARN": "🟡", "ERROR": "🔴", "SUCCESS": "✅"}
    print(f"{colors.get(level, '⚪')} [{datetime.now().strftime('%H:%M:%S')}] {msg}")

def fetch_and_clean_images(query, index):
    """Downloads, verifies, and RE-SAVES images to kill blue screen glitches."""
    raw_dir = f"raw_imgs_{index}"
    clean_dir = f"clean_imgs_{index}"
    for d in [raw_dir, clean_dir]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)
    
    # Using your preferred search key format
    main_term = query.split('|')[0].strip()
    log(f"Searching for: {main_term}", "INFO")
    
    crawler = BingImageCrawler(storage={'root_dir': raw_dir}, log_level=50)
    crawler.crawl(keyword=f"{main_term} trending 2026", max_num=6)
    
    time.sleep(3) # Wait for OS file release
    
    valid_paths = []
    for f in sorted(os.listdir(raw_dir)):
        raw_p = os.path.join(raw_dir, f)
        clean_p = os.path.join(clean_dir, f"fixed_{f}.jpg")
        try:
            with Image.open(raw_p) as img:
                rgb_img = img.convert('RGB')
                rgb_img.save(clean_p, "JPEG", quality=95)
                valid_paths.append(clean_p)
                log(f"   Cleaned & Validated: {f}", "SUCCESS")
        except:
            continue
    return valid_paths

def create_subtitles(text, duration):
    sentences = [s.strip() for s in text.replace('!', '.').replace('?', '.').split('.') if len(s.strip()) > 5]
    total_chars = sum(len(s) for s in sentences)
    bar = ColorClip(size=(W, TICKER_H), color=(150, 0, 0)).set_duration(duration).set_position(('center', H-TICKER_H))
    
    clips = [bar]
    curr_t = 0
    for s in sentences:
        s_dur = (len(s) / total_chars) * duration
        txt = TextClip(s, fontsize=32, color='white', font='Arial-Bold', method='caption', 
                       size=(W-100, TICKER_H-40), align='center').set_start(curr_t).set_duration(s_dur).set_position(('center', H-TICKER_H+20))
        clips.append(txt)
        curr_t += s_dur
    return clips

def generate_video(json_file):
    if not os.path.exists(json_file):
        log(f"Error: {json_file} not found.", "ERROR")
        return
    
    with open(json_file, "r", encoding="utf-8") as f: 
        items = json.load(f)

    all_scenes = []
    for i, item in enumerate(items):
        log(f"--- Processing News Item {i+1} of {len(items)} ---")
        voice_p = f"v_{i}.mp3"
        
        # Audio Generation
        full_speech = f"{item['hook_text']}. {item['headline']}. {item['details']}"
        gTTS(text=full_speech, lang='en').save(voice_p)
        audio = AudioFileClip(voice_p)
        dur = audio.duration

        # Visuals
        img_paths = fetch_and_clean_images(item.get('search_key', ''), i)
        if img_paths:
            clips = [ImageClip(p).set_duration(4).resize(height=IMAGE_ZONE_H).crossfadein(0.5) for p in img_paths]
            slideshow = concatenate_videoclips(clips, method="compose").loop(duration=dur).set_position(('center', IMAGE_ZONE_Y))
        else:
            slideshow = ColorClip(size=(W-60, IMAGE_ZONE_H), color=(25, 25, 45)).set_duration(dur).set_position(('center', IMAGE_ZONE_Y))

        header = TextClip(item['hook_text'].upper(), fontsize=38, color='yellow', font='Arial-Bold', size=(W-80, 150), method='caption').set_duration(dur).set_position(('center', HEADER_Y))
        footer = create_subtitles(item['details'], dur)
        
        bg = ColorClip(size=(W, H), color=(10, 10, 15)).set_duration(dur)
        scene = CompositeVideoClip([bg, header, slideshow] + footer).set_audio(audio)
        all_scenes.append(scene)

    log("Stitching all scenes...", "INFO")
    final = concatenate_videoclips(all_scenes, method="chain")
    
    # CTA Only on last scene
    cta = TextClip("Tune with us for more news", fontsize=36, color='white', bg_color='darkred', size=(W, 100), method='caption'
                   ).set_start(final.duration-4).set_duration(4).set_position(('center', H-400))
    
    final_v = CompositeVideoClip([final, cta])
    
    if os.path.exists(BGM_PATH):
        bgm = AudioFileClip(BGM_PATH).volumex(0.1).set_duration(final_v.duration)
        final_v = final_v.set_audio(CompositeAudioClip([final_v.audio, bgm]))

    output_filename = f"Automated_News_{datetime.now().strftime('%H%M')}.mp4"
    final_v.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac")
    
    # Cleanup audio temp files
    for i in range(len(items)):
        if os.path.exists(f"v_{i}.mp3"): os.remove(f"v_{i}.mp3")

    log(f"Video Complete: {output_filename}", "SUCCESS")

    # --- UPLOAD TRIGGER ---
    full_video_path = os.path.abspath(output_filename)
    choice = input(f"\n🚀 Video ready. Upload {output_filename} to YouTube as Private? (y/n): ").lower().strip()
    
    if choice in ['y', 'yes']:
        try:
            from stage3_upload import upload_from_json
            upload_from_json(json_file, video_file=full_video_path)
            log("Upload Successful!", "SUCCESS")
        except Exception as e:
            log(f"Upload logic failed: {e}", "ERROR")

if __name__ == "__main__":
    generate_video("news_data.json")