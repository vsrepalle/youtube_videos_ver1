import os
import tkinter as tk
from tkinter import filedialog
from stage3_upload import upload_from_json

def pick_and_upload():
    # 1. Setup File Picker
    root = tk.Tk()
    root.withdraw() # Hide main tkinter window
    
    print("📂 Please select the MP4 video file...")
    video_path = filedialog.askopenfilename(title="Select Video", filetypes=[("Video files", "*.mp4")])
    
    if not video_path:
        print("🔴 Upload cancelled. No file selected.")
        return

    print("📂 Please select the JSON metadata file...")
    json_path = filedialog.askopenfilename(title="Select JSON", filetypes=[("JSON files", "*.json")])
    
    if not json_path:
        print("🔴 Upload cancelled. No JSON selected.")
        return

    # 2. Trigger Upload
    print(f"🚀 Uploading {os.path.basename(video_path)} as Private...")
    try:
        upload_from_json(json_path, video_file=video_path)
        print("✅ Upload successful!")
    except Exception as e:
        print(f"🔴 Upload failed: {e}")

if __name__ == "__main__":
    pick_and_upload()