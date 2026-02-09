import os
import requests
import json

# 1. WINDOWS CONFIGURATION
os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"

# Use absolute paths for fonts to avoid "cannot open resource" errors
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT_REG = r"C:\Windows\Fonts\arial.ttf"

from moviepy import ImageClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip

# 2. YOUR SETTINGS
PEXELS_API_KEY = 'Oszdsq7V3DU1S8t1n6coHlHHeHb76cxZjb1HRYYvru32CpQYSmrO52ax'

# Today's News Data
NEWS_DATA = {
    "day": "Thursday",
    "date": "2026-01-29",
    "location": "Vanasthalipuram, Telangana, India",
    "is_news": True,
    "headline": "Vanasthalipuram Student Wins National AI Innovation Prize",
    "details": "A 19-year-old student from Vanasthalipuram has trended today for inventing a low-cost AI drone. Residents are sharing the news with pride this Thursday. Tune with us for more such news.",
    "tune_message": "Tune with us for more such news."
}

def download_image(location):
    print(f"🔍 Searching for image: {location}...")
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/v1/search?query={location}&per_page=1&orientation=portrait"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        if data.get('photos'):
            img_url = data['photos'][0]['src']['portrait']
            with open("temp_image.jpg", "wb") as f:
                f.write(requests.get(img_url).content)
            return "temp_image.jpg"
    except Exception as e:
        print(f"❌ Image Error: {e}")
    return None

def create_news_short(data):
    img_path = download_image(data['location'])
    if not img_path: return

    print("🎬 Rendering Video with Audio & Enhanced Visibility...")
    
    try:
        # Background Image
        bg = ImageClip(img_path).with_duration(10).resized(height=1920)

        # 1. Headline - With Black Bar for visibility
        headline_text = TextClip(
            text=data['headline'].upper(), font_size=65, color='white',
            method='caption', size=(900, None), font=FONT_BOLD,
            horizontal_align='center'
        ).with_position(('center', 250)).with_duration(10)

        # 2. Details - Added a semi-transparent background for readability
        details_txt = TextClip(
            text=data['details'], font_size=42, color='white',
            method='caption', size=(800, None), font=FONT_REG,
            horizontal_align='center'
        ).with_position(('center', 750)).with_duration(10)
        
        # Create a darkened box behind the details to make it readable
        detail_bg = ColorClip(size=(900, 400), color=(0,0,0)).with_opacity(0.6).with_position(('center', 700)).with_duration(10)

        # 3. CTA (Bottom)
        cta = TextClip(
            text=data['tune_message'], font_size=55, color='yellow', font=FONT_BOLD,
            bg_color='red'
        ).with_position(('center', 1650)).with_duration(10)

        # Final Assembly
        video = CompositeVideoClip([bg, detail_bg, headline_text, details_txt, cta])
        
        # --- AUDIO HANDLING ---
        # Ensure 'background_music.mp3' exists in your folder
        audio_path = "background_music.mp3"
        if os.path.exists(audio_path):
            print(f"🎵 Adding Audio: {audio_path}")
            audio = AudioFileClip(audio_path).with_duration(10)
            video = video.with_audio(audio)
        else:
            print("⚠️ No audio found! Place 'background_music.mp3' in the folder.")

        output_file = f"Short_{data['date']}.mp4"
        video.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac")
        
        print(f"✅ SUCCESS! Created: {os.path.abspath(output_file)}")
        print("Tune with us for more such news.")

    except Exception as e:
        print(f"❌ Rendering error: {e}")

if __name__ == "__main__":
    create_news_short(NEWS_DATA)