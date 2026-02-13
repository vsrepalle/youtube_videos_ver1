import os
import json
import time
from tqdm import tqdm
from google import genai
from google.genai import types
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type

# Setup Client
client = genai.Client(api_key="PASTE_YOUR_ACTUAL_API_KEY_HERE")

# --- NEW: RETRY LOGIC ---
# This decorator will retry the function if a 429 error occurs
@retry(
    wait=wait_random_exponential(multiplier=1, max=60), 
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(Exception) # You can refine this to specifically catch ClientError
)
def safe_generate_content(category):
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    return client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            tools=[grounding_tool],
            response_mime_type="application/json",
            system_instruction="You are a professional news producer. Output only valid JSON."
        ),
        contents=f"Search for latest {category} news today. Create a script JSON with 5 scenes. Mention 'tune with us for more such news'."
    )

def automate_news_bot(category):
    print(f"\n🚀 STARTING: {category.upper()}")
    
    # 1. Generate Script with Retry Logic
    try:
        response = safe_generate_content(category)
        news_data = json.loads(response.text)
        print(f"✅ JSON Script Generated.")
    except Exception as e:
        print(f"❌ Failed after retries: {e}")
        return

    # 2. Generate Clips with Throttling (Sleep 2s between clips to avoid 429)
    os.makedirs("scene_videos", exist_ok=True)
    for i, scene in enumerate(tqdm(news_data['scenes'], desc="Video Production")):
        video_response = client.models.generate_videos(
            model="veo-3.1-fast",
            prompt=scene['image_prompt'],
            config=types.GenerateVideosConfig(duration_seconds=5)
        )
        video_response.generated_videos[0].video.save(f"scene_videos/scene_{i}.mp4")
        time.sleep(2) # <--- ADDED: Small pause to respect RPM limits
            
    print(f"✅ Done!")

if __name__ == "__main__":
    automate_news_bot("T20 World Cup cricket")