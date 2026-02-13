import os, json, shutil, requests
import numpy as np
from datetime import datetime
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from icrawler.builtin import BingImageCrawler
import video_effects as fx 
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()

# --- 1. CONFIGURATION ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

try:
    # UPDATED: Ensure your stage3_upload can accept a custom filename
    from stage3_upload import upload_from_json
except ImportError:
    upload_from_json = None

BGM_PATH = "bg_music.mp3"
W, H = 1080, 1920

def fetch_image_from_pexels(query, index):
    """Fetches a high-quality image from Pexels API."""
    if not PEXELS_API_KEY:
        print("⚠️ Pexels API Key missing in .env. Skipping Pexels...")
        return None
        
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
    headers = {"Authorization": PEXELS_API_KEY}
    
    try:
        response = requests.get(url, headers=headers).json()
        if response.get('photos'):
            img_url = response['photos'][0]['src']['large2x']
            img_data = requests.get(img_url).content
            save_path = f"temp_pexels_{index}.jpg"
            with open(save_path, 'wb') as f:
                f.write(img_data)
            print(f"✅ Pexels image fetched for: {query}")
            return save_path
    except Exception as e:
        print(f"❌ Pexels API Error: {e}")
    return None

def fetch_image_from_bing(query, index):
    """Fallback: Uses Bing icrawler if Pexels fails."""
    save_dir = f"temp_images_{index}"
    if os.path.exists(save_dir): shutil.rmtree(save_dir)
    os.makedirs(save_dir)
    
    print(f"🚀 Falling back to Bing for: {query}...")
    try:
        bing_crawler = BingImageCrawler(storage={'root_dir': save_dir}, log_level=50)
        bing_crawler.crawl(keyword=query, max_num=1, filters={'size': 'large'})
        files = os.listdir(save_dir)
        if files: return os.path.join(save_dir, files[0])
    except Exception as e:
        print(f"⚠️ Bing Crawler failed: {e}")
    return None

def get_dynamic_background(item, index, voice_duration):
    """Waterfall logic: Pexels -> Bing -> Local -> Placeholder."""
    query = item.get('search_key', '').split('|')[0].strip()
    image_path = fetch_image_from_pexels(query, index)
    
    if not image_path:
        image_path = fetch_image_from_bing(query, index)
        
    if image_path:
        return ImageClip(image_path).resize(height=H).set_duration(voice_duration)

    bg_image = "temp_bg.jpg"
    if os.path.exists(bg_image):
        return ImageClip(bg_image).resize(height=H).set_duration(voice_duration)
    
    placeholder = np.zeros((H, W, 3), dtype=np.uint8)
    placeholder[:, :] = [20, 20, 40] 
    return ImageClip(placeholder).set_duration(voice_duration)

def generate_video_and_upload(json_file):
    if not os.path.exists(json_file): return
    
    # 2. GENERATE TIMESTAMPED FILENAME
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_video = f"TrendWave_{timestamp}.mp4"

    with open(json_file, "r", encoding="utf-8") as f: 
        items = json.load(f)

    scenes = []
    for i, item in enumerate(items):
        tts_text = f"{item['hook_text']}. {item['headline']}. {item['details']}"
        tts_file = f"voice_{i}.mp3"
        gTTS(text=tts_text, lang='en').save(tts_file)
        voice = AudioFileClip(tts_file)
        
        bg_layer = get_dynamic_background(item, i, voice.duration)
        bg_layer = fx.apply_ken_burns(bg_layer, zoom_ratio=0.05)
        
        scrolling_text = fx.create_sentence_scrolling(item['details'], voice.duration, W, H)
        hook = TextClip(item['hook_text'], fontsize=100, color='yellow', font='Arial-Bold', 
                        method='caption', size=(W-100, 300)).set_position(('center', 200)).set_duration(voice.duration)

        scene = CompositeVideoClip([bg_layer, hook, scrolling_text], size=(W, H)).set_audio(voice)
        scenes.append(scene)

    final_video = concatenate_videoclips(scenes, method="compose")
    if os.path.exists(BGM_PATH):
        final_video = fx.add_background_audio(final_video, BGM_PATH)

    # 3. LAST SCENE ONLY: CTA
    cta = TextClip("Tune with us for more such news", fontsize=55, color='white', font='Arial-Bold'
                  ).set_start(final_video.duration - 3.5).set_duration(3.5).set_position(('center', 1600))
    
    final_comp = CompositeVideoClip([final_video, cta])
    
    # Render the video
    print(f"🎬 Rendering {output_video}...")
    final_comp.write_videofile(output_video, fps=24, codec="libx264")
    
    # 4. CRITICAL FIX: Pass the ACTUAL filename to the uploader
    if upload_from_json:
        print(f"🚀 Uploading {output_video}...")
        upload_from_json(json_file, video_file=output_video)

if __name__ == "__main__":
    generate_video_and_upload("news_data.json")