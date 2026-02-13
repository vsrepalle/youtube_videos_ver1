import os, json, shutil, asyncio, requests
from edge_tts import Communicate
from moviepy.editor import *
import moviepy.video.fx.all as vfx
from moviepy.config import change_settings
from icrawler.builtin import BingImageCrawler

# YouTube API Imports
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload

# --- 1. CONFIGURATION ---
IM_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IM_PATH})
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Voice Profiles
VOICES = {
    "anchor": "en-US-LiamNeural",
    "storyteller": "en-GB-SoniaNeural"
}

async def generate_voice(text, filename, voice_type="anchor"):
    communicate = Communicate(text, VOICES[voice_type], rate="+15%") # 1.15x speed at source
    await communicate.save(filename)

def get_youtube_service():
    if not os.path.exists('client_secrets.json'):
        print("Error: client_secrets.json missing.")
        return None
    flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
    creds = flow.run_local_server(port=0)
    return build('youtube', 'v3', credentials=creds)

def fetch_bg_image(query, index):
    temp_dir = f"bg_{index}"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    try:
        crawler = BingImageCrawler(storage={'root_dir': temp_dir})
        crawler.crawl(keyword=query, max_num=1, filters=dict(size='large', layout='tall'))
        for f in os.listdir(temp_dir): return os.path.join(temp_dir, f)
    except: return None

async def create_master_short(json_file, voice_mode="anchor"):
    if not os.path.exists(json_file): return None
    with open(json_file, "r") as f: items = json.load(f)

    W, H = 1080, 1920
    scenes = []
    
    bg_music = AudioFileClip("bg_music.mp3").volumex(0.12) if os.path.exists("bg_music.mp3") else None

    for i, item in enumerate(items):
        # 1. Professional Voice Generation
        tts_file = f"voice_{i}.mp3"
        await generate_voice(f"{item['headline']}. {item['details']}", tts_file, voice_mode)
        voice = AudioFileClip(tts_file)
        dur = voice.duration

        # 2. Image Processing (No-Crop / Contain)
        bg_file = fetch_bg_image(item['search_key'], i)
        if bg_file:
            img = ImageClip(bg_file).resize(width=W)
            if img.h > H: img = img.resize(height=H)
            bg = img.on_color(size=(W, H), color=(0,0,0), pos='center').set_duration(dur)
        else:
            bg = ColorClip(size=(W, H), color=(20, 20, 40), duration=dur)

        # 3. Clear Text UI
        header_bar = ColorClip(size=(W, 320), color=(0,0,0)).set_opacity(0.85).set_position('top').set_duration(dur)
        footer_bar = ColorClip(size=(W, 350), color=(0,0,0)).set_opacity(0.85).set_position('bottom').set_duration(dur)
        
        txt_top = TextClip(item['headline'], fontsize=80, color='yellow', font='Arial-Bold', method='caption', size=(W-100, 280)).set_duration(dur).set_position(('center', 20))
        txt_bot = TextClip(item['details'], fontsize=48, color='white', font='Arial-Bold', method='caption', size=(W-120, 310)).set_duration(dur).set_position(('center', H-330))

        scene = CompositeVideoClip([bg, header_bar, footer_bar, txt_top, txt_bot], size=(W, H)).set_audio(voice).set_duration(dur)
        scenes.append(scene)

    final_video = concatenate_videoclips(scenes, method="compose")
    
    # Progress Bar & Music
    total_dur = final_video.duration
    if bg_music:
        final_video = final_video.set_audio(CompositeAudioClip([final_video.audio, bg_music.set_duration(total_dur)]))

    def make_progress_bar(t): return ColorClip(size=(max(1, int((t/total_dur)*W)), 20), color=(255, 0, 0)).get_frame(t)
    prog_bar = VideoClip(make_progress_bar, duration=total_dur).set_position(('left', 'top'))
    
    # Strict Last Scene Rule
    cta = TextClip("Tune with us for more such news", fontsize=55, color='white', font='Arial-Bold').set_start(total_dur - 2.5).set_duration(2.5).set_position(('center', 1300))

    final_comp = CompositeVideoClip([final_video, prog_bar, cta])
    output = f"TrendWave_{voice_mode}_V29.mp4"
    final_comp.write_videofile(output, fps=24, codec="libx264", audio_codec="aac", ffmpeg_params=["-pix_fmt", "yuv420p"])
    
    return output

def upload_to_youtube(file_path):
    youtube = get_youtube_service()
    if not youtube: return
    body = {'snippet': {'title': 'Trending Update 2026 | #Shorts', 'description': 'Tune with us for more such news.', 'categoryId': '25'}, 'status': {'privacyStatus': 'private'}}
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media).execute()
    print("✅ Uploaded!")

if __name__ == "__main__":
    choice = input("Select Voice (1: Anchor, 2: Storyteller): ")
    v_mode = "anchor" if choice == "1" else "storyteller"
    
    video_file = asyncio.run(create_master_short("news_data.json", v_mode))
    
    if video_file and input("Upload to YouTube? (y/n): ").lower() == 'y':
        upload_to_youtube(video_file)