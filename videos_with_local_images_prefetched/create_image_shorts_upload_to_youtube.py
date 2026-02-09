import os
import sys
import json
import shutil
import subprocess
from gtts import gTTS
from icrawler.builtin import BingImageCrawler
from PIL import Image

# --- PILLOW FIX ---
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, TextClip, CompositeVideoClip, CompositeAudioClip
from moviepy.video.fx.all import crop
from moviepy.config import change_settings

# 🛠️ YOUR IMAGEMAGICK PATH
YOUR_MAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
if os.path.exists(YOUR_MAGICK_PATH):
    change_settings({"IMAGEMAGICK_BINARY": YOUR_MAGICK_PATH})

def run_production(json_file):
    if not os.path.exists(json_file):
        print(f"❌ JSON file {json_file} not found.")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    TARGET_W, TARGET_H = 1080, 1920
    video_name = data.get('video_name', 'VIRAL_SHORT.mp4')
    video_path = os.path.abspath(video_name)
    assets_dir = os.path.abspath('temp_assets')
    bgm_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "High Noon - The Grey Room _ Density & Time.mp3")

    if os.path.exists(assets_dir): shutil.rmtree(assets_dir)
    os.makedirs(assets_dir, exist_ok=True)
    
    all_scene_clips = []

    for scene in data['scenes']:
        sid, txt = scene['id'], scene['text']
        search_term = scene.get('search_key', 'latest news')
        print(f"🎬 Processing Scene {sid} | 🔍 Search: {search_term}")
        
        # 1. Download Image
        scene_dir = os.path.join(assets_dir, f"s_{sid}")
        os.makedirs(scene_dir, exist_ok=True)
        crawler = BingImageCrawler(storage={'root_dir': scene_dir})
        crawler.crawl(keyword=search_term, max_num=1, filters=dict(size='large'))
        
        # 2. Audio Generation (Hindi)
        audio_path = os.path.join(assets_dir, f"audio_{sid}.mp3")
        gTTS(text=txt, lang='hi').save(audio_path) 
        voice_audio = AudioFileClip(audio_path)

        # 🎵 --- 🚀 BGM MIXING LOGIC ---
        if os.path.exists(bgm_file):
            bg_music = AudioFileClip(bgm_file).volumex(0.12) # 12% Volume for Music
            # Ensure BGM isn't shorter than voice
            if bg_music.duration < voice_audio.duration:
                bg_music = bg_music.loop(duration=voice_audio.duration)
            else:
                bg_music = bg_music.subclip(0, voice_audio.duration)
            
            final_audio = CompositeAudioClip([voice_audio.volumex(1.0), bg_music])
        else:
            print("⚠️ No 'bgm.mp3' found. Using voice only.")
            final_audio = voice_audio

        # 3. Image Processing
        img_files = [os.path.join(scene_dir, f) for f in os.listdir(scene_dir) if f.lower().endswith(('.jpg', '.png'))]
        if img_files:
            bg_temp = os.path.join(scene_dir, "processed.jpg")
            with Image.open(img_files[0]) as img:
                img.convert("RGB").save(bg_temp)
            
            bg_clip = ImageClip(bg_temp).set_duration(voice_audio.duration).set_audio(final_audio)
            w, h = bg_clip.size
            scale = max(TARGET_W/w, TARGET_H/h)
            bg_clip = bg_clip.resize(scale)
            bg_clip = crop(bg_clip, width=TARGET_W, height=TARGET_H, x_center=bg_clip.w/2, y_center=bg_clip.h/2)

            # 4. 🔥 CENTERED TEXT
            txt_clip = TextClip(
                txt, fontsize=85, color='yellow', font='Arial-Bold', 
                stroke_color='black', stroke_width=3, method='caption', 
                size=(TARGET_W * 0.9, None)
            ).set_duration(voice_audio.duration).set_position('center')

            all_scene_clips.append(CompositeVideoClip([bg_clip, txt_clip]))

    if all_scene_clips:
        print("🔗 Merging and exporting...")
        final_video = concatenate_videoclips(all_scene_clips, method="compose")
        final_video.write_videofile(video_path, fps=30, codec="libx264", audio_codec="aac")
        
        # --- UPLOADER HANDOFF ---
        uploader_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload_video.py")
        if os.path.exists(uploader_script):
            if input(f"\n🚀 Video ready! Upload to YouTube? (y/n): ").lower() == 'y':
                meta = data.get('metadata', {})
                subprocess.run([
                    sys.executable, uploader_script,
                    "--file", video_path,
                    "--title", meta.get('title', f"News {video_name}"),
                    "--description", meta.get('description', "tune with us for more such news"),
                    "--tags", meta.get('tags', "news, shorts")
                ])
                print("tune with us for more such news")

if __name__ == "__main__":
    run_production("bollywood_scenes.json")