import os, json, re, time, subprocess
import numpy as np
from PIL import Image, ImageFilter
from gtts import gTTS
from icrawler.builtin import BingImageCrawler

# --- YOUTUBE API IMPORTS ---
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

# --- MOVIEPY CONFIG ---
IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
os.environ["IMAGEMAGICK_BINARY"] = IMAGEMAGICK_BINARY

from moviepy.editor import (
    ImageClip, TextClip, ColorClip, 
    CompositeVideoClip, concatenate_videoclips, 
    AudioFileClip, CompositeAudioClip
)
import moviepy.video.fx.all as vfx

VIDEO_SIZE = (1080, 1920)

# --- 1. UTILITIES ---
def download_missing_image(keyword, target_dir):
    abs_target_dir = os.path.abspath(target_dir)
    if not os.path.exists(abs_target_dir):
        os.makedirs(abs_target_dir, exist_ok=True)
    print(f"🔍 Crawling for: {keyword}...")
    crawler = BingImageCrawler(storage={'root_dir': abs_target_dir})
    crawler.crawl(keyword=keyword, max_num=1)
    time.sleep(2)

def get_full_vertical_image(path):
    try:
        img = Image.open(path).convert("RGB")
    except:
        img = Image.new('RGB', (1080, 1080), color=(20, 40, 80))
    bg = img.resize(VIDEO_SIZE, Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(radius=25))
    img_ratio, screen_ratio = img.width / img.height, VIDEO_SIZE[0] / VIDEO_SIZE[1]
    if img_ratio > screen_ratio:
        new_w, new_h = VIDEO_SIZE[0], int(VIDEO_SIZE[0] / img_ratio)
    else:
        new_h, new_w = VIDEO_SIZE[1], int(VIDEO_SIZE[1] * img_ratio)
    nw, nh = int(new_w * 1.15), int(new_h * 1.15)
    img_res = img.resize((nw, nh), Image.Resampling.LANCZOS)
    bg.paste(img_res, ((VIDEO_SIZE[0] - nw) // 2, (VIDEO_SIZE[1] - nh) // 2))
    return np.array(bg)

# --- 2. YOUTUBE UPLOAD ENGINE (PRIVATE BY DEFAULT) ---
def trigger_youtube_upload(video_file, metadata):
    print("🔐 Initializing YouTube OAuth2...")
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    secret_file = next((f for f in os.listdir('.') if f.startswith('client_secret') and f.endswith('.json')), None)
    if not secret_file:
        print("❌ client_secret.json missing!")
        return
    flow = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
    credentials = flow.run_local_server(port=0)
    youtube = build("youtube", "v3", credentials=credentials)
    body = {
        'snippet': {
            'title': metadata.get('title', 'TrendWave News Update'), 
            'description': metadata.get('description', 'Subscribe to TrendWave Now!'), 
            'tags': metadata.get('tags', '').split(','), 
            'categoryId': '17'
        },
        'status': {
            'privacyStatus': 'private', # PRIVATE BY DEFAULT
            'selfDeclaredMadeForKids': False
        }
    }
    insert_request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True))
    response = insert_request.execute()
    print(f"✅ SUCCESS! Video ID: {response['id']} (Status: PRIVATE)")

# --- 3. PRODUCTION ENGINE ---
def generate_video(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    output_filename = data.get("video_name", "Cricket_Update.mp4")
    meta = data.get("metadata", {})
    clips = []

    # Persistent Branding Banner
    brand_banner = TextClip(txt='Please like and subscribe "TrendWave Now" Channel', 
                            font="Arial-Bold", fontsize=40, color="white", 
                            bg_color="blue", size=(1080, 80)).set_position(("center", 1840))

    for i, scene in enumerate(data["scenes"]):
        star = scene["star_name"]
        img_dir = os.path.join("media_bank", scene["category"], star.replace(" ", "_").lower())
        if not os.path.exists(img_dir) or not os.listdir(img_dir):
            download_missing_image(f"{star} cricket", img_dir)
        
        files = os.listdir(img_dir)
        img_path = os.path.join(img_dir, files[0]) if files else "NONE"
        
        # Audio
        voice_file = f"voice_{i}.mp3"
        gTTS(text=re.sub(r"\[.*?\]", "", scene["text"]), lang='en').save(voice_file)
        audio = AudioFileClip(voice_file).fx(vfx.speedx, 1.15)
        duration = audio.duration + 0.5

        # Visuals
        img_array = get_full_vertical_image(img_path)
        img_clip = ImageClip(img_array).set_duration(duration).set_audio(audio)
        
        header = TextClip(txt=meta.get("breaking_news_header", "CRICKET NEWS"), font="Arial-Bold", fontsize=70, color="yellow", bg_color="black", size=(1080, 150)).set_position(("center", 100)).set_duration(duration)
        
        # Scrolling Ticker
        ticker_text = f"  ::: {scene['text'].upper()} :::  "
        ticker = TextClip(txt=ticker_text, font="Arial-Bold", fontsize=50, color="white", bg_color="red").set_duration(duration)
        w, h = ticker.size
        ticker_scroll = ticker.set_position(lambda t: (VIDEO_SIZE[0] - (VIDEO_SIZE[0] + w) * (t / duration), 1680))
        
        clips.append(CompositeVideoClip([img_clip, header, ticker_scroll, brand_banner.set_duration(duration)]))

    # Engagement Slide
    if "poll_data" in data:
        bg_p = ColorClip(VIDEO_SIZE, color=(20, 20, 30)).set_duration(8)
        p_txt = TextClip(txt=f"POLL: {data['poll_data']['question']}", font="Arial-Bold", fontsize=55, color="yellow", method="caption", size=(950, None)).set_position(("center", 300)).set_duration(8)
        opts = TextClip(txt="\n\n".join(data['poll_data']['options']), font="Arial-Bold", fontsize=45, color="white").set_position(("center", 600)).set_duration(8)
        comm = TextClip(txt=data['comment_engagement']['comment_question'], font="Arial-Bold", fontsize=45, color="cyan", bg_color="black", size=(950, 200)).set_position(("center", 1400)).set_duration(8)
        clips.append(CompositeVideoClip([bg_p, p_txt, opts, comm, brand_banner.set_duration(8)]))

    # Dedicated Subscription End Frame
    end_bg = ColorClip(VIDEO_SIZE, color=(10, 10, 10)).set_duration(5)
    end_txt = TextClip(txt="PLEASE SUBSCRIBE\nTrendWave Now", font="Arial-Bold", fontsize=80, color="white", method="caption", size=(900, None)).set_position("center").set_duration(5)
    clips.append(CompositeVideoClip([end_bg, end_txt]))

    final = concatenate_videoclips(clips, method="compose")
    
    # Background Music
    if os.path.exists("background.mp3"):
        bg_m = AudioFileClip("background.mp3").volumex(0.12).set_duration(final.duration)
        final = final.set_audio(CompositeAudioClip([final.audio, bg_m]))

    final.write_videofile(output_filename, fps=24)
    os.startfile(output_filename)
    
    if input("🚀 Upload? (y/n): ").lower() == 'y':
        trigger_youtube_upload(output_filename, meta)

if __name__ == "__main__":
    generate_video("news_production.json")