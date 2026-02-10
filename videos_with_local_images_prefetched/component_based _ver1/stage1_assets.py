import os, json, re, sys, shutil
from gtts import gTTS
from icrawler.builtin import BingImageCrawler

def prepare_assets(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Clean media bank for fresh run
    if os.path.exists("media_bank"):
        shutil.rmtree("media_bank")

    for i, scene in enumerate(data["scenes"]):
        img_dir = f"media_bank/scene_{i}"
        os.makedirs(img_dir, exist_ok=True)

        query_input = scene.get('search_key', "")
        
        # New Requirement Logic: Split-Screen Detection
        if "|" in query_input:
            # Handle two distinct stars for top/bottom layout
            sub_queries = [q.strip() for q in query_input.split("|")]
            print(f"🌓 Split-Screen detected for Scene {i}")
            for j, sub_q in enumerate(sub_queries[:2]): # Limit to 2 for top/bottom
                print(f"  🔍 Crawling Star {j+1}: {sub_q}")
                # We download 1 best image per star to avoid confusion
                crawler = BingImageCrawler(storage={'root_dir': img_dir})
                crawler.crawl(keyword=sub_q, max_num=1)
        else:
            # Standard Single Search Logic
            query = query_input if query_input else f"{scene.get('star_name', 'News')} 2026 hd"
            print(f"🔍 Crawling Scene {i}: {query}")
            crawler = BingImageCrawler(storage={'root_dir': img_dir})
            crawler.crawl(keyword=query, max_num=3)
        
        # Audio Generation
        text_clean = re.sub(r"\[.*?\]", "", scene["text"])
        gTTS(text=text_clean, lang='en').save(f"v_{i}.mp3")
    print("\n✅ Assets Prepared for Split-Screen Rendering.")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "vijay_jananayagan_optimized.json"
    prepare_assets(target)