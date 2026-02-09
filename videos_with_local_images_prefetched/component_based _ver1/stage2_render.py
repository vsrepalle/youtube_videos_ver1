import os, json, sys, numpy as np
from PIL import Image, ImageOps
from moviepy.config import change_settings
from moviepy.editor import (ImageClip, TextClip, CompositeVideoClip, 
                            concatenate_videoclips, AudioFileClip, 
                            vfx, CompositeAudioClip)

change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})

# VERTICAL RESOLUTION (Shorts/TikTok/Reels)
VIDEO_SIZE = (1080, 1920)

def get_vertical_frame(path):
    """Resizes and crops image to fit 1080x1920 perfectly."""
    img = Image.open(path).convert("RGB")
    # Resizes and crops to fill the vertical screen (Cover mode)
    img = ImageOps.fit(img, VIDEO_SIZE, Image.Resampling.LANCZOS)
    return np.array(img)

def render_video(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    clips = []
    # Subscription bar adjusted for vertical width
    sub_bar = TextClip(txt="Subscribe TrendWave Now", font="Arial-Bold", fontsize=50, 
                       color="white", bg_color="red", size=(1080, 80)).set_position(("center", 1750))

    for i, scene in enumerate(data["scenes"]):
        # 1. Prepare Voiceover
        voice_audio = AudioFileClip(f"v_{i}.mp3").fx(vfx.speedx, 1.1)
        duration = voice_audio.duration + 0.5
        
        # 2. Subtitles for Vertical (Centered lower-middle)
        txt = (TextClip(txt=scene["text"], font="Arial-Bold", fontsize=60, color="yellow", 
                        bg_color="black", method='caption', size=(950, None))
               .set_duration(duration)
               .set_position(('center', 1150))) 

        # 3. Background Image
        img_folder = f"media_bank/scene_{i}"
        img_list = [os.path.join(img_folder, f) for f in os.listdir(img_folder) if f.endswith(('.jpg', '.png'))]
        img_path = img_list[0] 
        bg = ImageClip(get_vertical_frame(img_path)).set_duration(duration)
        
        clips.append(CompositeVideoClip([bg, txt, sub_bar.set_duration(duration)]).set_audio(voice_audio))

    # Combine all scenes
    final_video = concatenate_videoclips(clips, method="compose").resize(newsize=VIDEO_SIZE)

    # 4. Add Background Music (Looping and Volume Adjustment)
    if os.path.exists("bg_music.mp3"):
        bg_music = AudioFileClip("bg_music.mp3").volumex(0.15) # 15% volume for background
        # Loop music if it's shorter than the video
        bg_music = bg_music.fx(vfx.loop, duration=final_video.duration)
        
        # Merge background music with the scene voiceovers
        final_audio = CompositeAudioClip([final_video.audio, bg_music])
        final_video = final_video.set_audio(final_audio)

    # Export Video
    output_name = data.get("video_name", "T20_WorldCup_Update_Vertical.mp4")
    final_video.write_videofile(output_name, fps=24, threads=4, preset="ultrafast")
    print(f"✅ Video Rendered: {output_name}")

if __name__ == "__main__":
    # Ensure you have bg_music.mp3 in the same folder
    render_video(sys.argv[1] if len(sys.argv) > 1 else "t20_worldcup_today.json")