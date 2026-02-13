import os, json, shutil, requests
from gtts import gTTS
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

def get_youtube_service():
    """Triggers the browser login for YouTube permission."""
    if not os.path.exists('client_secrets.json'):
        print("Error: client_secrets.json not found in directory.")
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

def create_automated_short(json_file):
    if not os.path.exists(json_file): return None
    with open(json_file, "r") as f: items = json.load(f)

    W, H = 1080, 1920
    scenes = []
    SPEED_FACTOR = 1.15  # <--- Added as requested
    
    # Check for Background Music
    bg_music_clip = AudioFileClip("bg_music.mp3").volumex(0.12) if os.path.exists("bg_music.mp3") else None

    for i, item in enumerate(items):
        # 1. Voice Generation
        tts_text = f"{item['headline']}. {item['details']}"
        tts_file = f"voice_{i}.mp3"
        gTTS(text=tts_text, lang='en').save(tts_file)
        voice = AudioFileClip(tts_file)
        
        # 2. Image Processing (No-Crop / Contain Mode)
        bg_file = fetch_bg_image(item['search_key'], i)
        if bg_file:
            # Contain: Resizes to width 1080, then pads top/bottom with black if needed
            img = ImageClip(bg_file).resize(width=W)
            if img.h > H: img = img.resize(height=H)
            bg = img.on_color(size=(W, H), color=(0,0,0), pos='center')
        else:
            bg = ColorClip(size=(W, H), color=(20, 20, 40))

        # 3. Visible Text UI
        header_bar = ColorClip(size=(W, 320), color=(0,0,0)).set_opacity(0.85).set_position('top')
        footer_bar = ColorClip(size=(W, 350), color=(0,0,0)).set_opacity(0.85).set_position('bottom')
        
        txt_top = TextClip(item['headline'], fontsize=80, color='yellow', font='Arial-Bold', method='caption', size=(W-100, 280)).set_position(('center', 20))
        txt_bot = TextClip(item['details'], fontsize=48, color='white', font='Arial-Bold', method='caption', size=(W-120, 310)).set_position(('center', H-330))

        # 4. Scene Assembly & Speedup
        scene = CompositeVideoClip([bg, header_bar, footer_bar, txt_top, txt_bot], size=(W, H)).set_audio(voice).set_duration(voice.duration)
        scenes.append(scene.fx(vfx.speedx, SPEED_FACTOR))

    # 5. Master Concatenation
    final_video = concatenate_videoclips(scenes, method="compose")
    total_dur = final_video.duration

    # 6. Audio Ducking (Music + Voice)
    if bg_music_clip:
        looped_bg = afx.audio_loop(bg_music_clip, duration=total_dur)
        final_audio = CompositeAudioClip([final_video.audio, looped_bg])
        final_video = final_video.set_audio(final_audio)

    # 7. Overlays: Progress Bar & Final CTA
    def make_progress_bar(t):
        return ColorClip(size=(max(1, int((t/total_dur)*W)), 20), color=(255, 0, 0)).get_frame(t)
    
    prog_bar = VideoClip(make_progress_bar, duration=total_dur).set_position(('left', 'top'))
    
    # Strict Last Scene Rule for CTA
    cta = TextClip("Tune with us for more such news", fontsize=55, color='white', font='Arial-Bold').set_start(total_dur - 2.5).set_duration(2.5).set_position(('center', 1300))

    final_comp = CompositeVideoClip([final_video, prog_bar, cta])
    
    output_name = "TrendWave_V28_1.15x.mp4"
    final_comp.write_videofile(output_name, fps=24, codec="libx264", audio_codec="aac", ffmpeg_params=["-pix_fmt", "yuv420p"])
    
    # 8. Cleanup Temporary Files
    for i in range(len(items)): 
        if os.path.exists(f"voice_{i}.mp3"): os.remove(f"voice_{i}.mp3")
        
    return output_name

def upload_to_youtube(file_path):
    youtube = get_youtube_service()
    if not youtube: return

    body = {
        'snippet': {
            'title': 'Viral AI & Celeb Update 2026 | #Shorts',
            'description': 'Latest trending news updates on TrendWave AI. Tune with us for more!',
            'tags': ['News', 'AI', 'Ayesha Khan', 'Cricket'],
            'categoryId': '25'
        },
        'status': {'privacyStatus': 'private'}
    }
    
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
    print("Uploading to YouTube...")
    response = request.execute()
    print(f"✅ Success! Video ID: {response['id']}")

if __name__ == "__main__":
    # Ensure you have your news_data.json ready
    video_file = create_automated_short("news_data.json")
    
    if video_file:
        confirm = input(f"Short '{video_file}' is ready. Proceed to YouTube upload? (y/n): ")
        if confirm.lower() == 'y':
            upload_to_youtube(video_file)