import subprocess
import json
import os

def run_step(step_name, command):
    print(f"\n====================\n🚀 INITIATING: {step_name}\n====================")
    choice = input(f"▶️ Start {step_name}? (y/n): ").lower()
    if choice == 'y':
        result = subprocess.run(command)
        if result.returncode != 0:
            print(f"\n❌ ERROR in {step_name} (Exit Code: {result.returncode})")
            return False
    return True

def main():
    json_path = "tabu_marriage_myth.json" # Change this for Cricket news
    
    # STEP 1: Assets (Images/Voice)
    if not run_step("Asset Preparation", ["python", "stage1_assets.py", json_path]): return

    # STEP 2: Rendering
    if not run_step("Video Rendering", ["python", "stage2_render.py", json_path]): return

    # STEP 3: YouTube Upload (Fixed Argument Passing)
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        video_file = data.get("video_name", "output.mp4")
        video_title = data.get("metadata", {}).get("title", "Breaking News Update")
        
        upload_cmd = ["python", "stage3_upload.py", "--file", video_file, "--title", video_title]
        if not run_step("YouTube Upload", upload_cmd): return

    print("\n🏁 Pipeline Finished Successfully.")

if __name__ == "__main__":
    main()