import os, json, re, sys, shutil
from gtts import gTTS
from icrawler.builtin import BingImageCrawler

def prepare_assets(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if os.path.exists("media_bank"):
        shutil.rmtree("media_bank")

    for i, scene in enumerate(data["scenes"]):
        img_dir = f"media_bank/scene_{i}"
        os.makedirs(img_dir, exist_ok=True)

        # Robust search logic: uses search_key if exists, else builds one safely
        query = scene.get('search_key')
        if not query:
            star = scene.get('star_name', 'News')
            loc = scene.get('location', '')
            query = f"{star} {loc} 2026 hd".strip()
        
        print(f"🔍 Crawling: {query}")
        crawler = BingImageCrawler(storage={'root_dir': img_dir})
        crawler.crawl(keyword=query, max_num=3)
        
        text_clean = re.sub(r"\[.*?\]", "", scene["text"])
        gTTS(text=text_clean, lang='en').save(f"v_{i}.mp3")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "t20_worldcup_today.json"
    prepare_assets(target)