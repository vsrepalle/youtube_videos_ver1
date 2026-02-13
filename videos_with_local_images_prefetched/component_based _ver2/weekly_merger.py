import os
import datetime
import numpy as np
from PIL import Image, ImageFilter
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip, vfx

def blur_frame(image):
    """ Blurs a frame using PIL (Pillow) """
    # Convert numpy array to PIL Image
    pil_img = Image.fromarray(image)
    # Apply Gaussian Blur (Radius 15 for strong effect)
    blurred_pil = pil_img.filter(ImageFilter.GaussianBlur(radius=15))
    # Convert back to numpy array
    return np.array(blurred_pil)

def create_roundup():
    archive_dir = "exports/weekly_archive"
    if not os.path.exists(archive_dir):
        return print(f"❌ Archive directory not found: {archive_dir}")

    # Get all mp4 files in the archive
    files = sorted([os.path.join(archive_dir, f) for f in os.listdir(archive_dir) if f.endswith(".mp4")])
    
    if not files: 
        return print("⏭️ No shorts found in archive to merge!")

    print(f"🎬 Merging {len(files)} clips into Roundup...")
    processed_clips = []
    
    for f in files:
        try:
            short = VideoFileClip(f)
            
            # 1. Create blurred background (16:9)
            # Resize short to fill width, then blur
            bg = (short.resize(width=1920)
                  .fl_image(blur_frame) 
                  .fx(vfx.lum_contrast, -0.3, 0, 0)) # Make it darker
            
            # 2. Overlay the original vertical short in the center
            fg = short.set_position("center").resize(height=1080)
            
            # Combine them
            combined = CompositeVideoClip([bg, fg], size=(1920, 1080)).set_duration(short.duration)
            processed_clips.append(combined)
            print(f"✅ Processed: {os.path.basename(f)}")
            
        except Exception as e:
            print(f"⚠️ Skipping {f} due to error: {e}")

    if processed_clips:
        output_name = f"Weekly_Roundup_{datetime.datetime.now().strftime('%b_%d')}.mp4"
        final = concatenate_videoclips(processed_clips, method="compose")
        
        # Write the final long-form video
        final.write_videofile(output_name, fps=24, codec="libx264", audio_codec="aac")
        
        # Keep archive for now to be safe, or uncomment to auto-delete:
        # for f in files: os.remove(f)
        print(f"✨ DONE! Roundup saved as: {output_name}")

if __name__ == "__main__":
    create_roundup()