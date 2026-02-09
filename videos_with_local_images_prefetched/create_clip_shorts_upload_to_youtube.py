import os
import requests
import json
import shutil
from gtts import gTTS
from PIL import Image
# --- PATCH FOR PILLOW ---
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, vfx

PEXELS_API_KEY = 'Oszdsq7V3DU1S8t1n6coHlHHeHb76cxZjb1HRYYvru32CpQYSmrO52ax' # Get this for free from Pexels.com

def download_pexels_video(query, save_path):
    headers = {'Authorization': PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=1&orientation=portrait"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data['videos']:
            # Get the highest quality mobile-friendly link
            video_url = data['videos'][0]['video_files'][0]['link']
            r = requests.get(video_url, stream=True)
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk: f.write(chunk)
            return True
    return False

def run_production(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    TARGET_W, TARGET_H = 1080, 1920
    assets_dir = 'temp_assets'
    if os.path.exists(assets_dir): shutil.rmtree(assets_dir)
    os.makedirs(assets_dir)
    
    all_clips = []

    for scene in data['scenes']:
        sid, txt, query = scene['id'], scene['text'], scene['query']
        print(f"🎬 Processing Scene {sid}: {query}")

        # 1. Download Video Clip
        video_path = os.path.join(assets_dir, f"video_{sid}.mp4")
        success = download_pexels_video(query, video_path)
        
        if success:
            # 2. Audio Generation
            audio_path = os.path.join(assets_dir, f"audio_{sid}.mp3")
            gTTS(text=txt, lang='en').save(audio_path)
            audio = AudioFileClip(audio_path)

            # 3. Clip Processing
            clip = VideoFileClip(video_path).without_audio()
            
            # Loop or trim video to match audio length
            if clip.duration < audio.duration:
                clip = clip.fx(vfx.loop, duration=audio.duration)
            else:
                clip = clip.subclip(0, audio.duration)
            
            clip = clip.set_audio(audio).resize(width=TARGET_W)
            # Ensure vertical center crop
            clip = clip.crop(x_center=clip.w/2, y_center=clip.h/2, width=TARGET_W, height=TARGET_H)
            all_clips.append(clip)

    if all_clips:
        final = concatenate_videoclips(all_clips, method="compose")
        final.write_videofile(data['video_name'], fps=30, codec="libx264")
        print("✅ Viral-style video complete! tune with us for more such news")

if __name__ == "__main__":
    run_production("bollywood_scenes.json")