import os
import json
import sys
from icrawler.builtin import BingImageCrawler

DEFAULT_JSON = "stars_data.json" # Still uses your stars_data.json as source

def dynamic_bulk_download_shorts(json_file):
    if not os.path.exists(json_file):
        print(f"❌ Error: {json_file} not found.")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # --- NEW BASE DIRECTORY FOR SHORTS IMAGES ---
    base_dir = "bollywood_star_short_images"
    os.makedirs(base_dir, exist_ok=True)

    print(f"\n🚀 Starting Short-Specific Image Download to '{base_dir}'...")

    for star_info in data.get('stars', []):
        star_name = star_info.get('name')
        movies = star_info.get('last_5_movies', [])
        if not star_name: continue

        star_safe_name = star_name.replace(" ", "_").lower()
        star_folder = os.path.join(base_dir, star_safe_name)
        os.makedirs(star_folder, exist_ok=True)

        print(f"\n🌟 Processing Star: {star_name} for Shorts")

        # --- STEP 1: FETCH FALLBACK PROFILE IMAGE (for Shorts) ---
        profile_filename = f"{star_safe_name}_iconic_short.jpg" # Unique name for shorts profile
        profile_path = os.path.join(star_folder, profile_filename)
        
        if not os.path.exists(profile_path):
            print(f"  📸 Fetching Profile Image for Shorts...")
            temp_dir = os.path.join(star_folder, "temp_profile")
            os.makedirs(temp_dir, exist_ok=True)
            
            crawler = BingImageCrawler(storage={'root_dir': temp_dir})
            crawler.crawl(
                keyword=f"{star_name} iconic rich look portrait vertical high resolution", 
                max_num=1, 
                filters=dict(layout='tall', size='large') # Prioritize tall images
            )
            
            dl_files = os.listdir(temp_dir)
            if dl_files:
                os.replace(os.path.join(temp_dir, dl_files[0]), profile_path)
                print(f"  💾 Saved Profile: {profile_filename}")
            else:
                print(f"  ⚠️ Could not find profile image for {star_name}.")
            os.rmdir(temp_dir)
        else:
            print(f"  ✅ Profile Image for Shorts already exists.")

        # --- STEP 2: FETCH MOVIE-SPECIFIC IMAGES (for Shorts) ---
        for movie in movies:
            movie_safe = movie.replace(" ", "_").lower()
            new_filename = f"{star_safe_name}_{movie_safe}_short.jpg" # Unique name for shorts movie
            final_path = os.path.join(star_folder, new_filename)

            if os.path.exists(final_path):
                print(f"  ✅ Movie Image for Shorts exists: {movie}")
                continue

            print(f"  🎬 Fetching Movie Image for Shorts: {movie}...")
            temp_dir = os.path.join(star_folder, "temp_movie")
            os.makedirs(temp_dir, exist_ok=True)

            crawler = BingImageCrawler(storage={'root_dir': temp_dir})
            crawler.crawl(
                keyword=f"{star_name} in movie {movie} rich look vertical high resolution movie poster", 
                max_num=1, 
                filters=dict(layout='tall', size='large') # Prioritize tall images
            )

            dl_files = os.listdir(temp_dir)
            if dl_files:
                os.replace(os.path.join(temp_dir, dl_files[0]), final_path)
                print(f"  💾 Saved Movie: {new_filename}")
            else:
                print(f"  ⚠️ Could not find movie image for {star_name} in {movie}.")
            os.rmdir(temp_dir)

    print("\n✅ Shorts-Specific Image Bank Update Complete!")
    print("tune with us for more such news")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSON
    dynamic_bulk_download_shorts(target_file)