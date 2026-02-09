import os
import json
from icrawler.builtin import BingImageCrawler

def check_and_download(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    base_dir = "bollywood_star_bank"
    os.makedirs(base_dir, exist_ok=True)

    # Contextual check: Iterate through scenes to find required stars/movies
    for scene in data['scenes']:
        star = scene.get('star_name', '').replace(" ", "_").lower()
        movie = scene.get('movie_name', '').replace(" ", "_").lower()
        
        if not star: continue
        
        star_dir = os.path.join(base_dir, star)
        os.makedirs(star_dir, exist_ok=True)
        filename = f"{star}_{movie}.jpg" if movie else f"{star}_iconic.jpg"
        filepath = os.path.join(star_dir, filename)

        if not os.path.exists(filepath):
            print(f"🔍 Asset missing: {filename}. Fetching now...")
            crawler = BingImageCrawler(storage={'root_dir': star_dir})
            query = f"{scene.get('star_name')} in {scene.get('movie_name')} rich look high res"
            crawler.crawl(keyword=query, max_num=1, filters=dict(size='large'))
            
            # Rename icrawler's default 000001.jpg to our naming convention
            for f in os.listdir(star_dir):
                if f.startswith("000001"):
                    os.rename(os.path.join(star_dir, f), filepath)
        else:
            print(f"✅ Asset exists: {filename}")

if __name__ == "__main__":
    import sys
    check_and_download(sys.argv[1])