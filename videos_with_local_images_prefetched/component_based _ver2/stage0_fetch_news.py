import os
import json
import argparse
from google import genai
from google.genai import types

# Initialize Gemini Client
client = genai.Client(api_key="YOUR_GEMINI_API_KEY")

def generate_daily_json(category):
    print(f"🌐 Searching for {category} updates (Feb 11, 2026)...")
    
    # The prompt now uses the dynamic 'category' variable
    prompt = (
        f"Search for the latest {category} today, Feb 11, 2026. "
        "Create a 1-minute video script JSON with 5 scenes. "
        "Ensure search_keys follow the format: 'Star Name | Star Name'. "
        "End the last scene with: 'tune with us for more such news'."
    )

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearchRetrieval())],
            response_mime_type="application/json",
            system_instruction="You are a professional news editor. Output only valid JSON."
        ),
        contents=prompt
    )

    # Naming the file based on category to avoid overwrites
    safe_name = category.replace(" ", "_").lower()
    json_filename = f"mega_{safe_name}_feb11.json"
    
    with open(json_filename, "w", encoding="utf-8") as f:
        f.write(response.text)
    
    print(f"✅ Daily JSON generated: {json_filename}")
    return json_filename

if __name__ == "__main__":
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Generate daily news JSON.")
    parser.add_argument(
        "--category", 
        type=str, 
        default="T20 World Cup cricket", # Default behavior
        help="The news category to fetch (e.g., 'Bollywood', 'Stock Market')"
    )
    
    args = parser.parse_args()
    generate_daily_json(args.category)