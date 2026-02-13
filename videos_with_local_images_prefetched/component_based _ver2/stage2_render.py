import os, json, sys, numpy as np
from PIL import Image, ImageOps, ImageDraw
from moviepy.config import change_settings
from moviepy.editor import (ImageClip, TextClip, CompositeVideoClip, 
                            concatenate_videoclips, AudioFileClip, 
                            vfx)

# 1. ImageMagick Path (Update if necessary)
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})

VIDEO_SIZE = (1080, 1920)

def get_horizontal_frame_with_divider(img_paths):
    """Creates a side-by-side frame with a white divider and shadow."""
    combined = Image.new("RGB", VIDEO_SIZE, (20, 20, 20)) # Dark background
    slot_size = (535, 1920) # Slightly smaller for the divider space
    
    if len(img_paths) >= 2:
        img_l = ImageOps.pad(Image.open(img_paths[0]).convert("RGB"), slot_size, color="black")
        img_r = ImageOps.pad(Image.open(img_paths[1]).convert("RGB"), slot_size, color="black")
        
        combined.paste(img_l, (0, 0))
        combined.paste(img_r, (545, 0))
        
        # Draw white divider
        draw = ImageDraw.Draw(combined)
        draw.rectangle([538, 0, 542, 1920], fill="white") 
        return np.array(combined)
    
    elif len(img_paths) == 1:
        img = ImageOps.pad(Image.open(img_paths[0]).convert("RGB"), VIDEO_SIZE, color="black")
        return np.array(img)
    return np.zeros((1920, 1080, 3), dtype=np.uint8)

def render_video(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    scenes = data.get("scenes", [])
    clips = []
    sub_bar = TextClip("Please subscribe Trendwave Now", font="Arial-Bold", fontsize=45, 
                       color="white", bg_color="red", size=(1080, 80)).set_position(("center", 1800))

    for i, scene in enumerate(scenes):
        audio_path = f"v_{i}.mp3"
        duration = AudioFileClip(audio_path).duration + 0.5 if os.path.exists(audio_path) else 5.0
        
        # Background with split-screen
        img_folder = f"media_bank/scene_{i}"
        img_list = [os.path.join(img_folder, f) for f in os.listdir(img_folder) if f.endswith(('.jpg', '.png'))] if os.path.exists(img_folder) else []
        bg = ImageClip(get_horizontal_frame_with_divider(img_list)).set_duration(duration)
        
        # Subtitles with scroll
        txt_clip = TextClip(scene.get("content", ""), font="Arial-Bold", fontsize=50, color="yellow", 
                            bg_color="black", method='caption', size=(950, None)).set_duration(duration).set_position(('center', 1300))
        
        scene_comp = CompositeVideoClip([bg, txt_clip, sub_bar.set_duration(duration)])
        if os.path.exists(audio_path):
            scene_comp = scene_comp.set_audio(AudioFileClip(audio_path).fx(vfx.speedx, 1.1))
        
        clips.append(scene_comp)

    # FINAL SPEED BOOST (1.15x)
    final_video = concatenate_videoclips(clips, method="compose").resize(newsize=VIDEO_SIZE).fx(vfx.speedx, 1.15)
    
    # CRITICAL: Filename must match what Stage 3 expects
    output_name = f"{data.get('id')}.mp4" 
    final_video.write_videofile(output_name, fps=24, codec="libx264")
    return output_name

if __name__ == "__main__":
    render_video(sys.argv[1])