import os, json, shutil, time
from datetime import datetime
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from PIL import Image
from icrawler.builtin import BingImageCrawler
import moviepy.video.fx.all as vfx

# --- CONFIGURATION ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

W, H = 720, 1280 
BGM_PATH = "bg_music.mp3"

# --- INTERNAL FUNCTIONS ---

def apply_ken_burns(clip, zoom_ratio=0.03):
    return clip.fx(vfx.resize, lambda t: 1.0 + (zoom_ratio * t))

def create_news_ticker_with_subtitles(full_text, duration):
    """Creates a Red Bar, FIXED Progress Bar, and SYNCED subtitles."""
    sentences = full_text.replace('!', '.').replace('?', '.').split('.')
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    
    # 1. Red News Bar (Slightly taller for better text spacing)
    news_bar = ColorClip(size=(W, 240), color=(180, 0, 0)).set_duration(duration).set_position(('center', H-240))
    
    # 2. FIXED Progress Bar (Using a dedicated update function to avoid OpenCV 0-size error)
    def make_progress_bar(t):
        # Calculate width: min 1 pixel, max W pixels
        current_w = max(1, int(W * (t / duration)))
        return ColorClip(size=(current_w, 12), color=(255, 255, 255)).get_frame(t)

    prog_bar = VideoClip(make_progress_bar, duration=duration).set_position((0, H-12))

    # 3. Synced Text Clips
    text_clips = []
    if sentences:
        each_dur = duration / len(sentences)
        for i, sentence in enumerate(sentences):
            txt = TextClip(sentence, fontsize=34, color='white', font='Arial-Bold',
                           method='caption', size=(W-120, 180), align='center'
                           ).set_duration(each_dur).set_start(i * each_dur).set_position(('center', H-230))
            text_clips.append(txt)
        
    return CompositeVideoClip([news_bar, prog_bar] + text_clips, size=(W, H))

def fetch_and_prepare_images(query, index):
    save_dir = f"temp_imgs_{index}"
    if os.path.exists(save_dir): shutil.rmtree(save_dir)
    os.makedirs(save_dir)
    crawler = BingImageCrawler(storage={'root_dir': save_dir}, log_level=50)
    search_term = query.split('|')[0].strip()
    crawler.crawl(keyword=f"{search_term} cricket match 4k", max_num=3)
    
    valid_paths = []
    for f in os.listdir(save_dir):
        p = os.path.join(save_dir, f)
        try:
            with Image.open(p) as img:
                img.convert('RGB').save(p)
                valid_paths.append(p)
        except: continue
    return valid_paths

# --- MAIN GENERATOR ---

def generate_video_and_upload(json_file):
    if not os.path.exists(json_file): return
    
    output_video = f"Breaking_News_{datetime.now().strftime('%H%M')}.mp4"
    with open(json_file, "r", encoding="utf-8") as f: 
        items = json.load(f)

    scenes = []
    for i, item in enumerate(items):
        print(f"🎬 Processing Scene {i+1}...")
        
        # Audio
        tts_text = f"{item['hook_text']}. {item['headline']}. {item['details']}"
        tts_file = f"voice_{i}.mp3"
        gTTS(text=tts_text, lang='en').save(tts_file)
        voice = AudioFileClip(tts_file)
        dur = voice.duration

        # Image Border (Fixed overlap - Moved lower and added margin)
        images = fetch_and_prepare_images(item.get('search_key', ''), i)
        if images:
            img_clips = [ImageClip(p).set_duration(dur/len(images)).resize(width=W-80) for p in images]
            bg_content = concatenate_videoclips(img_clips, method="chain").set_position(('center', 320))
            bg_content = apply_ken_burns(bg_content)
        else:
            bg_content = ColorClip(size=(W-80, 450), color=(20, 20, 40)).set_duration(dur).set_position(('center', 320))

        # Header (Now strictly in the upper 'safe zone')
        header = TextClip(item['headline'].upper(), fontsize=38, color='yellow', font='Arial-Bold',
                          method='caption', size=(W-100, 150), bg_color='black').set_duration(dur).set_position(('center', 80))

        # Footer & Bar
        footer = create_news_ticker_with_subtitles(item['details'], dur)
        canvas = ColorClip(size=(W, H), color=(10, 10, 20)).set_duration(dur)

        scene = CompositeVideoClip([canvas, bg_content, header, footer], size=(W, H)).set_audio(voice)
        scenes.append(scene)

    if not scenes: return
    final = concatenate_videoclips(scenes, method="chain")
    
    # CTA - Last Scene
    cta = TextClip("Tune with us for more news", fontsize=36, color='white', font='Arial-Bold', 
                   bg_color='darkred').set_start(final.duration - 3.5).set_duration(3.5).set_position(('center', H-450))
    
    final_video = CompositeVideoClip([final, cta])

    # Music
    if os.path.exists(BGM_PATH):
        bgm = AudioFileClip(BGM_PATH).volumex(0.12).set_duration(final_video.duration)
        final_video = final_video.set_audio(CompositeAudioClip([final_video.audio, bgm]))

    print(f"🚀 Rendering with Progress Bar...")
    final_video.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac", 
                                threads=8, preset="ultrafast", logger='bar')

    # Upload
    choice = input(f"\nUpload {output_video} to YouTube as Private? (y/n): ").lower().strip()
    if choice in ['y', 'yes']:
        from stage3_upload import upload_from_json
        upload_from_json(json_file, video_file=output_video)

if __name__ == "__main__":
    generate_video_and_upload("news_data.json")