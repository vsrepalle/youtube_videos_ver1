import os
import shutil

def sync_to_social_folder(video_filename):
    # 1. Define your folders
    source = f"exports/{video_filename}"
    social_folder = "Social_Uploads"
    
    # 2. Create the folder if it doesn't exist
    if not os.path.exists(social_folder):
        os.makedirs(social_folder)
        print(f"📁 Created folder: {social_folder}")

    # 3. Move the file
    try:
        shutil.copy2(source, os.path.join(social_folder, video_filename))
        print(f"🚀 Success! {video_filename} is ready for Instagram/Facebook upload.")
    except Exception as e:
        print(f"⚠️ Sync failed: {e}")

# Example Usage (Call this after your video is rendered):
# sync_to_social_folder("Evening_Mega_Roundup_Feb10.mp4")