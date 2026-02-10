import os, json, sys, numpy as np
from PIL import Image, ImageOps
from moviepy.config import change_settings
from moviepy.editor import (ImageClip, TextClip, CompositeVideoClip, 
                            concatenate_videoclips, AudioFileClip, 
                            vfx, CompositeAudioClip)

# ImageMagick Path
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})

VIDEO_SIZE = (1080, 1920)

def get_vertical_frame(img_paths):
    """
    Handles both single images and split-screen (top/bottom).
    If img_paths has 2+ items, it stacks the first two.
    """
    if len(img_paths) >= 2:
        # Split-Screen Logic: Stack two images (1080x960 each)
        half_size = (1080, 960)
        img_top = Image.open(img_paths[0]).convert("RGB")
        img_bottom = Image.open(img_paths[1]).convert("RGB")
        
        img_top = ImageOps.fit(img_top, half_size, Image.Resampling.LANCZOS)
        img_bottom = ImageOps.fit(img_bottom, half_size, Image.Resampling.LANCZOS)
        
        combined = Image.new("RGB", VIDEO_SIZE)
        combined.paste(img_top, (0, 0))
        combined.paste(img_bottom, (0, 960))
        return np.array(combined)
    else:
        # Standard Single Image Logic
        img = Image.open(img_paths[0]).convert("RGB")
        img = ImageOps.fit(img, VIDEO_SIZE, Image.Resampling.LANCZOS)
        return np.array(img)

def render_video(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    clips = []
    sub_bar = TextClip(txt="Subscribe TrendWave Now", font="Arial-Bold", fontsize=50, 
                       color="white", bg_color="red", size=(1080, 80)).set_position(("center", 1750))

    for i, scene in enumerate(data["scenes"]):
        # 1. Prepare Voiceover
        voice_audio = AudioFileClip(f"v_{i}.mp3").fx(vfx.speedx, 1.1)
        duration = voice_audio.duration + 0.5
        
        # 2. Scrolling Subtitles Logic
        start_y = 1450
        end_y = 1100
        scroll_speed = (start_y - end_y) / duration

        txt = (TextClip(txt=scene["text"], font="Arial-Bold", fontsize=60, color="yellow", 
                        bg_color="black", method='caption', size=(950, None))
               .set_duration(duration)
               .set_position(lambda t: ('center', start_y - (scroll_speed * t))))

        # 3. Dynamic Background (Logic for Split-Screen)
        img_folder = f"media_bank/scene_{i}"
        img_list = [os.path.join(img_folder, f) for f in os.listdir(img_folder) if f.endswith(('.jpg', '.png'))]
        
        # If asset script downloaded 2 distinct star images, they will be stacked
        bg_frame = get_vertical_frame(img_list)
        bg = ImageClip(bg_frame).set_duration(duration)
        
        clips.append(CompositeVideoClip([bg, txt, sub_bar.set_duration(duration)]).set_audio(voice_audio))

    final_video = concatenate_videoclips(clips, method="compose").resize(newsize=VIDEO_SIZE)

    # 4. Background Music
    if os.path.exists("bg_music.mp3"):
        bg_music = AudioFileClip("bg_music.mp3").volumex(0.12).fx(vfx.loop, duration=final_video.duration)
        final_video = final_video.set_audio(CompositeAudioClip([final_video.audio, bg_music]))

    output_name = data.get("video_name", "TrendWave_Update_Vertical.mp4")
    final_video.write_videofile(output_name, fps=24, threads=4, preset="ultrafast")
    print(f"✅ Video Rendered: {output_name}")

if __name__ == "__main__":
    render_video(sys.argv[1] if len(sys.argv) > 1 else "vijay_jananayagan_optimized.json")