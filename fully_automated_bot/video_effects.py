import os
import numpy as np
from moviepy.editor import *
import moviepy.video.fx.all as vfx

def apply_ken_burns(clip, zoom_ratio=0.04):
    """Adds a smooth zoom-in effect to an image clip."""
    return clip.fx(vfx.resize, lambda t: 1.0 + (zoom_ratio * t))

def create_sentence_scrolling(full_text, duration, W, H):
    """Creates a scrolling effect that shows one sentence at a time."""
    # Split by common sentence enders
    sentences = full_text.replace('!', '.').replace('?', '.').split('.')
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    
    if not sentences:
        return TextClip(full_text, fontsize=50, color='white').set_duration(duration)

    each_dur = duration / len(sentences)
    clips = []
    
    for i, sentence in enumerate(sentences):
        # Create a "label" style text for a single sentence
        txt = TextClip(
            sentence, 
            fontsize=65, 
            color='white', 
            font='Arial-Bold',
            method='caption',
            size=(W-200, None),
            align='center',
            stroke_color='black',
            stroke_width=2
        ).set_start(i * each_dur).set_duration(each_dur).set_position(('center', 1100))
        
        # Subtle "float up" animation for each sentence
        txt = txt.set_position(lambda t, i=i: ('center', 1150 - (t * 20)))
        clips.append(txt)
        
    return CompositeVideoClip(clips, size=(W, H))

def add_background_audio(video_clip, bgm_path, volume=0.15):
    """Mixes background music with the voiceover."""
    if os.path.exists(bgm_path):
        bgm = AudioFileClip(bgm_path).volumex(volume).set_duration(video_clip.duration)
        if video_clip.audio:
            final_audio = CompositeAudioClip([video_clip.audio, bgm])
            return video_clip.set_audio(final_audio)
    return video_clip