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
    # SET JSON FILENAME HERE
    json_path = "t20_wc_breaking_feb10.json" 
    
    # STEP 1: Assets (Images/Voice)
    if not run_step("Asset Preparation", ["python", "stage1_assets.py", json_path]): return

    # STEP 2: Rendering
    if not run_step("Video Rendering", ["python", "stage2_render.py", json_path]): return

    # STEP 3: YouTube Upload
    if os.path.exists(json_path):
        # Now passing the json path directly to the upload script
        # This allows stage3_upload.py to handle title/description internally
        upload_cmd = ["python", "stage3_upload.py", "--json", json_path]
        if not run_step("YouTube Upload", upload_cmd): return

    print("\n🏁 Pipeline Finished Successfully.")

if __name__ == "__main__":
    main()