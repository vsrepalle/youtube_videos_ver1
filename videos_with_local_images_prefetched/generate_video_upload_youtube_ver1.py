import os, json, random, re, subprocess, time, sys
import numpy as np
from PIL import Image, ImageFilter
from gtts import gTTS

# --- YOUTUBE API IMPORTS ---
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

# --- MOVIEPY CONFIG ---
# Ensure this path matches your local ImageMagick installation
IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
os.environ["IMAGEMAGICK_BINARY"] = IMAGEMAGICK_BINARY

from moviepy.editor import (
    ImageClip, TextClip, ColorClip, 
    CompositeVideoClip, concatenate_videoclips, 
    AudioFileClip, CompositeAudioClip
)
import moviepy.video.fx.all as vfx

VIDEO_SIZE = (1080, 1920)

# --- 1. SCROLLING TICKER LOGIC ---
def create_scrolling_ticker(text, duration):
    """Creates a smooth red news ticker scrolling at the bottom."""
    scroll_text = "  ::: BREAKING NEWS ::: " + text.upper() + "          "
    txt_clip = TextClip(
        txt=scroll_text, font="Arial-Bold", fontsize=55,
        color="white", bg_color="red"
    ).set_duration(duration)
    
    w, h = txt_clip.size
    # Scroll from right (1080) to left (-w)
    ticker = txt_clip.set_position(lambda t: (VIDEO_SIZE[0] - (VIDEO_SIZE[0] + w) * (t / duration), 1800))
    return ticker

# --- 2. IMAGE PROCESSING (LETTERBOX WITH 1.15x BOOST) ---
def get_full_vertical_image(path):
    """Resizes image to fit screen with a blurred background and 1.15x scale."""
    img = Image.open(path).convert("RGB")
    bg = img.resize(VIDEO_SIZE, Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(radius=25))
    
    img_ratio = img.width / img.height
    screen_ratio = VIDEO_SIZE[0] / VIDEO_SIZE[1]
    
    if img_ratio > screen_ratio:
        new_w, new_h = VIDEO_SIZE[0], int(VIDEO_SIZE[0] / img_ratio)
    else:
        new_h, new_w = VIDEO_SIZE[1], int(VIDEO_SIZE[1] * img_ratio)
    
    # Apply the 1.15x extension boost as requested
    boost = 1.15 
    new_w, new_h = int(new_w * boost), int(new_h * boost)
    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    bg.paste(img_resized, ((VIDEO_SIZE[0] - new_w) // 2, (VIDEO_SIZE[1] - new_h) // 2))
    return np.array(bg)

# --- 3. ENGAGEMENT SCREEN ---
def create_engagement_clip(poll, comment, duration=7):
    """Creates a visual slide for Polls and Comments."""
    bg = ColorClip(VIDEO_SIZE, color=(20, 20, 30)).set_duration(duration)
    
    poll_title = TextClip(
        txt=f"POLL: {poll['question']}", font="Arial-Bold", fontsize=50,
        color="yellow", method="caption", size=(950, None)
    ).set_position(("center", 300)).set_duration(duration)
    
    options_txt = "\n\n".join([f"{i+1}. {opt}" for i, opt in enumerate(poll['options'])])
    options_clip = TextClip(
        txt=options_txt, font="Arial-Bold", fontsize=45,
        color="white", method="caption", size=(850, None)
    ).set_position(("center", 550)).set_duration(duration)
    
    cta_clip = TextClip(
        txt=f"{comment['comment_question']}\n\n{comment['comment_cta_text']}", 
        font="Arial-Bold", fontsize=45,
        color="cyan", method="caption", size=(950, None), bg_color="black"
    ).set_position(("center", 1350)).set_duration(duration)
    
    return CompositeVideoClip([bg, poll_title, options_clip, cta_clip])

# --- 4. YOUTUBE UPLOAD ENGINE (FUZZY FILE SEARCH) ---
def trigger_youtube_upload(video_file, metadata):
    print("🔐 Starting Authentication...")
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    
    # Detects client_secrets.json even if naming varies slightly
    folder_files = os.listdir('.')
    secret_file = next((f for f in folder_files if f.lower().startswith('client_secret')), None)

    if not secret_file:
        print(f"❌ ERROR: Credentials file not found. Folder contains: {folder_files}")
        return

    print(f"📂 Using credentials from: {secret_file}")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
        credentials = flow.run_local_server(port=0)
        youtube = build("youtube", "v3", credentials=credentials)

        request_body = {
            'snippet': {
                'title': metadata.get('title', 'Latest Bollywood Viral News'),
                'description': metadata.get('description', 'Check out the latest updates!'),
                'tags': metadata.get('tags', 'Bollywood,News,Viral').split(','),
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }

        print(f"📤 Uploading {video_file} to YouTube...")
        insert_request = youtube.videos().insert(
            part=','.join(request_body.keys()),
            body=request_body,
            media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True)
        )
        
        response = insert_request.execute()
        print(f"✅ UPLOAD SUCCESSFUL! Video ID: {response['id']}")
        print(f"🔗 View here: https://www.youtube.com/watch?v={response['id']}")
        
    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")

# --- 5. MAIN PRODUCTION ENGINE ---
def generate_video(json_file):
    if not os.path.exists(json_file):
        print(f"❌ Error: {json_file} not found.")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Resolve video name from top-level or metadata
    output_filename = data.get("video_name") or data.get("metadata", {}).get("video_name", "TrendWave_Output.mp4")
    meta = data.get("metadata", {})
    bg_music_file = "background.mp3"
    
    clips = []
    print(f"🎬 Processing scenes for: {output_filename}")

    for i, scene in enumerate(data["scenes"]):
        star_slug = scene["star_name"].replace(" ", "_").lower()
        # Look for the first image in the prefetched media folder
        img_dir = os.path.join("media_bank", scene["category"], star_slug)
        if os.path.exists(img_dir) and os.listdir(img_dir):
            img_path = os.path.join(img_dir, os.listdir(img_dir)[0])
        else:
            img_path = "generic.jpg"

        img_array = get_full_vertical_image(img_path)
        
        # Audio Generation
        voice_file = f"voice_{i}.mp3"
        clean_text = re.sub(r"\[.*?\]", "", scene["text"]).strip()
        gTTS(text=clean_text, lang='en').save(voice_file)
        voice = AudioFileClip(voice_file).fx(vfx.speedx, 1.15)
        duration = voice.duration + 0.5

        # Visual Assembly
        img_clip = ImageClip(img_array).set_duration(duration).set_audio(voice)
        header = TextClip(
            txt=meta.get("breaking_news_header", "TODAY'S BREAKING NEWS"), 
            font="Arial-Bold", fontsize=70, color="yellow", bg_color="black", size=(1080, 120)
        ).set_position(("center", 120)).set_duration(duration)
        
        ticker = create_scrolling_ticker(scene["text"], duration)
        clips.append(CompositeVideoClip([img_clip, header, ticker]))

    # Add Engagement Slide
    if "poll_data" in data and "comment_engagement" in data:
        print("📊 Adding Poll & Engagement screen...")
        clips.append(create_engagement_clip(data["poll_data"], data["comment_engagement"]))

    # Final "Tune with us" Outro
    outro_text = TextClip(
        txt="THANKS FOR WATCHING!\n\nTune with us for more such news",
        font="Arial-Bold", fontsize=70, color="white",
        method="caption", size=(900, None)
    ).set_position("center").set_duration(4)
    clips.append(CompositeVideoClip([ColorClip(VIDEO_SIZE, color=(10, 25, 45)).set_duration(4), outro_text]))

    # Concatenate and Mix Music
    final_video = concatenate_videoclips(clips, method="compose")
    
    if os.path.exists(bg_music_file):
        bg_audio = AudioFileClip(bg_music_file).volumex(0.12).set_duration(final_video.duration)
        final_video = final_video.set_audio(CompositeAudioClip([final_video.audio, bg_audio]))

    final_video.write_videofile(output_filename, fps=24, codec="libx264")
    
    # Auto-Preview
    os.startfile(output_filename)

    print("\n" + "="*40)
    print(f"✅ VIDEO READY: {output_filename}")
    print("="*40)
    
    # Upload Confirmation
    choice = input("🚀 Proceed with UPLOAD to YouTube? (y/n): ").lower().strip()
    if choice == 'y':
        trigger_youtube_upload(output_filename, meta)
    else:
        print("📁 Upload cancelled. Video saved locally.")

    print("\n💡 Reminder: Cricket news is doing amazingly good — let's keep that niche in mind!")

if __name__ == "__main__":
    generate_video("news_production.json")