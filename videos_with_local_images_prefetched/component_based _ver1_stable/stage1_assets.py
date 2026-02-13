import os, json, re, sys, shutil
from gtts import gTTS
from icrawler.builtin import BingImageCrawler

def prepare_assets(json_file):
    if not os.path.exists(json_file):
        print(f"❌ Error: {json_file} not found.")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Clean media bank for fresh run
    if os.path.exists("media_bank"):
        shutil.rmtree("media_bank")

    # Use 'scenes' or 'news' key
    scenes = data.get("scenes") or data.get("news") or []

    for i, scene in enumerate(scenes):
        img_dir = f"media_bank/scene_{i}"
        os.makedirs(img_dir, exist_ok=True)

        query_input = scene.get('search_key', "")
        
        # Split-Screen Detection logic
        if "|" in query_input:
            sub_queries = [q.strip() for q in query_input.split("|")]
            print(f"🌓 Split-Screen detected for Scene {i}")
            for j, sub_q in enumerate(sub_queries[:2]): 
                print(f"   🔍 Crawling Star {j+1}: {sub_q}")
                crawler = BingImageCrawler(storage={'root_dir': img_dir})
                crawler.crawl(keyword=sub_q, max_num=1)
        else:
            query = query_input if query_input else f"{scene.get('star_name', 'News')} 2026 hd"
            print(f"🔍 Crawling Scene {i}: {query}")
            crawler = BingImageCrawler(storage={'root_dir': img_dir})
            crawler.crawl(keyword=query, max_num=3)
        
        # FIXED: Audio Generation (Handles both 'content' and 'text')
        raw_text = scene.get("content") or scene.get("text") or "No content available"
        text_clean = re.sub(r"\[.*?\]", "", raw_text)
        
        print(f"🎙️ Generating Audio for Scene {i}...")
        try:
            tts = gTTS(text=text_clean, lang='en')
            tts.save(f"v_{i}.mp3")
        except Exception as e:
            print(f"⚠️ Audio Error: {e}")

    print("\n✅ Assets Prepared for Rendering.")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "news_11_feb.json"
    prepare_assets(target)