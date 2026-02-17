import os
import tkinter as tk
from tkinter import filedialog
# Updated Import: Matching your stage3_upload.py
from stage3_upload import get_authenticated_service, upload_from_json

def browse_file(title, file_types):
    """Opens explorer and returns the selected path."""
    root = tk.Tk()
    root.withdraw()  # Hide the small main tkinter window
    root.attributes("-topmost", True) # Bring the dialog to the front
    file_path = filedialog.askopenfilename(title=title, filetypes=file_types)
    root.destroy()
    return file_path

def manual_mode():
    print("\n" + "="*40)
    print(" 🛠️  MANUAL YOUTUBE UPLOADER (EXPLORER MODE) ")
    print("="*40)
    
    # 1. Select Video File
    print("📂 Please select your Video File...")
    video_path = browse_file("Select Video to Upload", [("Video Files", "*.mp4 *.mov *.avi"), ("All Files", "*.*")])
    if not video_path:
        print("🛑 No video selected. Exiting.")
        return
    print(f"✅ Selected Video: {os.path.basename(video_path)}")

    # 2. Select JSON File
    print("\n📄 Please select the Metadata JSON file...")
    json_path = browse_file("Select Metadata JSON", [("JSON Files", "*.json"), ("All Files", "*.*")])
    if not json_path:
        print("🛑 No JSON selected. Exiting.")
        return
    print(f"✅ Selected JSON: {os.path.basename(json_path)}")

    # 3. Channel and Index (Still manual for precision)
    print("\nTarget Channels: TrendWave Now | SpaceMind AI")
    chan = input("📺 Target Channel Name: ").strip()
    index = int(input("🔢 Enter scene index from JSON (usually 0, 1, or 2): "))

    print(f"\n⏳ Initializing upload for '{chan}'...")
    
    try:
        # Trigger the actual upload function from your stage3 script
        upload_from_json(json_path, video_file=video_path, index=index)
        print("\n" + "-"*40)
        print("✅ SUCCESS: Video is being processed by YouTube!")
        print("-"*40)

    except Exception as e:
        print(f"💥 An error occurred: {e}")

if __name__ == "__main__":
    manual_mode()