import os
import json
import numpy as np
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
import video_effects as fx

# --- IMAGEMAGICK FIX (Based on your screenshot) ---
# This tells MoviePy exactly where the rendering engine is located.
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

try:
    from stage3_upload import upload_from_json
except ImportError:
    upload_from_json = None

W, H = 1080, 1920
BGM_PATH = "bg_music.mp3"
DEFAULT_BG = "default_bg.jpg"


def create_gradient_background(duration):
    """Creates a smooth dark gradient background if no image is found."""
    gradient = np.zeros((H, W, 3), dtype=np.uint8)
    for y in range(H):
        color_value = int(20 + (60 * (y / H)))
        gradient[y, :, :] = (10, 20, color_value)
    return ImageClip(gradient).set_duration(duration)


def get_background_clip(data, duration):
    """Smart background loader."""
    image_path = data.get("image_path")
    if image_path and os.path.exists(image_path):
        print(f"🖼 Using image from JSON: {image_path}")
        return ImageClip(image_path).resize(height=H).set_duration(duration)
    if os.path.exists(DEFAULT_BG):
        print("🖼 Using default background image.")
        return ImageClip(DEFAULT_BG).resize(height=H).set_duration(duration)
    print("🎨 No background image found. Generating gradient background.")
    return create_gradient_background(duration)


def generate_video_and_upload(json_file):
    if not os.path.exists(json_file):
        print("❌ JSON file not found.")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        data_raw = json.load(f)

    items = data_raw if isinstance(data_raw, list) else [data_raw]
    data = items[0]

    video_filename = data.get("video_name", "SpaceMind_Final.mp4")

    if os.path.exists(video_filename):
        choice = input(f"⚡ '{video_filename}' exists. [U]pload or [R]e-create? ").strip().lower()
        if choice in ['u', 'y']:
            if upload_from_json:
                upload_from_json(json_file)
            return
        elif choice != 'r':
            return

    scenes = []

    for i, item in enumerate(items):
        # Extracting data from your updated JSON structure
        hook = item.get("hook_text", item.get("title", ""))
        headline = item.get("headline", item.get("category", ""))
        details = item.get("details", item.get("description", ""))

        tts_text = f"{hook}. {headline}. {details}"
        tts_file = f"voice_{i}.mp3"

        gTTS(text=tts_text, lang="en").save(tts_file)
        voice = AudioFileClip(tts_file)

        bg_layer = get_background_clip(item, voice.duration)
        bg_layer = fx.apply_ken_burns(bg_layer, zoom_ratio=0.05)

        # TextClip will now work because of the IMAGEMAGICK_BINARY fix above
        hook_clip = TextClip(
            hook,
            fontsize=95,
            color="yellow",
            font="Arial-Bold",
            method="caption",
            size=(W - 120, 300),
            align="center",
            stroke_color="black",
            stroke_width=3
        ).set_position(("center", 180)).set_duration(voice.duration)

        headline_clip = TextClip(
            headline,
            fontsize=65,
            color="white",
            font="Arial-Bold",
            method="caption",
            size=(W - 200, None),
            align="center",
            stroke_color="black",
            stroke_width=2
        ).set_position(("center", 420)).set_duration(voice.duration)

        scrolling_text = fx.create_sentence_scrolling(details, voice.duration, W, H)

        scene = CompositeVideoClip(
            [bg_layer, hook_clip, headline_clip, scrolling_text],
            size=(W, H)
        ).set_audio(voice)

        scene = fx.apply_speed_multiplier(scene, factor=1.05)
        scenes.append(scene)

    final_video = concatenate_videoclips(scenes, method="compose")
    final_video = fx.add_background_audio(final_video, BGM_PATH)

    # Closing CTA Scene
    cta_text = "Tune with us for more such news"
    cta = TextClip(
        cta_text,
        fontsize=55,
        color="white",
        font="Arial-Bold",
        stroke_color="black",
        stroke_width=2
    ).set_start(final_video.duration - 3.5).set_duration(3.5).set_position(("center", 1600))

    final_comp = CompositeVideoClip([final_video, cta])
    
    # Exporting as Private is handled by your upload script, 
    # but we ensure the video renders here first.
    final_comp.write_videofile(video_filename, fps=24, codec="libx264")

    if upload_from_json:
        upload_from_json(json_file)


if __name__ == "__main__":
    generate_video_and_upload("news_data.json")