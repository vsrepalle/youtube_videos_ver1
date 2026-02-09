import os
import json
import time
import sys
from google import genai
from google.genai import types

# ───────────────── CONFIGURATION ─────────────────
API_KEY = "AIzaSyBL9N16wmqZj8s-ft6ePmLBt4_GQ86BIqY"
client = genai.Client(api_key=API_KEY)

# Current stable model for 2026
MODEL_ID = "gemini-2.5-flash" 
ENGLISH_CHAPTERS = ["Nouns"] 
QUESTIONS_COUNT = 5 

def get_gemini_content(chapter_name, count):
    print(f"🤖 Requesting {count} questions for: {chapter_name}...")
    
    # Updated prompt to include your specific news requirements
    prompt = f"""
    Generate exactly {count} educational scripts for the English chapter: '{chapter_name}'.
    Format: id (string), topic (string), hook (string), bg_color (dark hex), font_color (light hex), 
    day (string), location (string), is_news (boolean),
    and scenes (array of 5 strings). 
    Ensure the last scene is always: 'Tune with us for more such news'.
    Return ONLY JSON.
    """

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema={
                        "type": "OBJECT",
                        "properties": {
                            "videos": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "id": {"type": "STRING"},
                                        "topic": {"type": "STRING"},
                                        "hook": {"type": "STRING"},
                                        "bg_color": {"type": "STRING"},
                                        "font_color": {"type": "STRING"},
                                        "day": {"type": "STRING"},
                                        "location": {"type": "STRING"},
                                        "is_news": {"type": "BOOLEAN"},
                                        "scenes": {"type": "ARRAY", "items": {"type": "STRING"}}
                                    },
                                    "required": ["id", "topic", "hook", "scenes", "day", "location", "is_news"]
                                }
                            }
                        }
                    }
                )
            )
            return json.loads(response.text).get("videos", [])

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 30 * (attempt + 1)
                print(f"⏳ Rate limit hit. Cooling down for {wait}s...")
                time.sleep(wait)
            else:
                print(f"⚠️ Error: {e}")
                break
    return []

def run_master_downloader():
    all_videos = []
    for chapter in ENGLISH_CHAPTERS:
        chapter_data = get_gemini_content(chapter, QUESTIONS_COUNT)
        if chapter_data:
            all_videos.extend(chapter_data)
            print(f"✅ Successfully harvested {len(chapter_data)} items.")
        time.sleep(5)

    if not all_videos:
        print("❌ No data collected. Check API Key or Model ID.")
        sys.exit(1)

    with open("viral_library.json", "w", encoding="utf-8") as f:
        json.dump({"videos": all_videos}, f, indent=4)
    
    print(f"\n📂 File Saved. Tune with us for more such news!")

if __name__ == "__main__":
    run_master_downloader()