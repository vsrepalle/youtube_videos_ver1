import os
import json
import shutil
import subprocess
from gtts import gTTS
from moviepy.editor import *
import moviepy.video.fx.all as vfx
from moviepy.config import change_settings
from icrawler.builtin import BingImageCrawler

# --- 1. CONFIGURATION ---
IM_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IM_PATH})

# News Context: February 12, 2026
news_items = [
    {
        "type": "Cricket",
        "headline": "Samson to Lead Powerplay?",
        "details": "With Abhishek Sharma doubtful, Sanju Samson is set to open vs Namibia tonight in Delhi.",
        "search_key": "Sanju Samson India Cricket T20 World Cup 2026"
    },
    {
        "type": "Movie",
        "headline": "Jana Nayagan Court Case Ends!",
        "details": "Madras HC dismissed the petition. Vijay's film moves to the Revising Committee for release.",
        "search_key": "Vijay Jana Nayagan Bobby Deol"
    }
]

def fetch_bg_image(query, index):
    temp_dir = f"bg_{index}"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    crawler = BingImageCrawler(storage={'root_dir': temp_dir})
    crawler.crawl(keyword=query, max_num=1, filters=dict(size='large', layout='tall'))
    for file in os.listdir(temp_dir): return os.path.join(temp_dir, file)
    return None

def create_short(items):
    W, H = 1080, 1920 
    scene_duration = 6 
    output_filename = "TrendWave_Short_Private.mp4"

    individual_scenes = []
    
    for i, item in enumerate(items):
        # 1. Audio Generation per scene
        text = f"{item['type']} Update! {item['headline']} {item['details']}"
        tts = gTTS(text=text, lang='en')
        tts_file = f"voice_{i}.mp3"
        tts.save(tts_file)
        voice = AudioFileClip(tts_file)

        # 2. Visuals per scene
        bg_file = fetch_bg_image(item['search_key'], i)
        bg = ImageClip(bg_file).set_duration(scene_duration).resize(newsize=(W, H)) if bg_file else ColorClip(size=(W, H), color=(20, 20, 40), duration=scene_duration)
        
        h_clip = TextClip(item['headline'], fontsize=85, color='yellow', font='Arial-Bold', method='caption', size=(W-100, None)).set_duration(scene_duration).set_position(('center', 300))
        d_clip = TextClip(item['details'], fontsize=50, color='white', font='Arial', method='caption', size=(W-150, None)).set_start(1).set_duration(scene_duration-1).set_position(('center', 750))
        
        # Combine into a single scene clip
        scene = CompositeVideoClip([bg, h_clip, d_clip]).set_audio(voice).set_duration(scene_duration)
        individual_scenes.append(scene)

    # 3. Concatenate Scenes (Prevents Collision)
    news_body = concatenate_videoclips(individual_scenes, method="compose")
    total_body_dur = news_body.duration

    # 4. Add Permanent Overlays & Last Scene CTA
    p_sub = TextClip("Please subscribe TrendWave Now", fontsize=40, color='cyan', font='Arial-Bold').set_duration(total_body_dur).set_position(('center', 1750))
    
    # Last Scene Overlay (only on the final part of the video)
    l_cta = TextClip("Tune with us for more such news", fontsize=50, color='white', font='Arial-Bold', method='caption', size=(W-100, None))\
        .set_start(total_body_dur - 2).set_duration(2).set_position(('center', 1500))

    # Assemble Final Video
    final_video = CompositeVideoClip([news_body, p_sub, l_cta])
    
    # Optional Background Music
    if os.path.exists("bg_music.mp3"):
        bg_music = AudioFileClip("bg_music.mp3").volumex(0.15).set_duration(total_body_dur)
        final_video.audio = CompositeAudioClip([final_video.audio, bg_music])

    # 5. Apply 1.15x Speed & Render
    fast_video = final_video.fx(vfx.speedx, 1.15)
    fast_video.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", ffmpeg_params=["-pix_fmt", "yuv420p"])
    
    # Cleanup
    fast_video.close()
    for i in range(len(items)):
        if os.path.exists(f"voice_{i}.mp3"):
            try: os.remove(f"voice_{i}.mp3")
            except: pass

    # Confirmation & Upload
    choice = input("\n🚀 Sequential Video Ready. Upload? (y/n): ").strip().lower()
    if choice in ['y', 'yes']:
        metadata_name = "sequential_update.json"
        with open(metadata_name, "w") as f:
            json.dump({"video_name": output_filename, "topic": "Cricket/Movie News", "description": "Sequential update. Tune with us for more such news."}, f)
        subprocess.run(["python", "stage3_upload.py", "--json", metadata_name], check=True)

if __name__ == "__main__":
    create_short(news_items)