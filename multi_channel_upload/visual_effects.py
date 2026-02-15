import os
from moviepy.editor import *
from PIL import Image, ImageDraw

def create_rounded_box(w, h, color, radius=40, opacity=230):
    """Creates a smooth rounded container for text backgrounds."""
    rect_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(rect_img)
    fill_color = color + (opacity,) 
    draw.rounded_rectangle([0, 0, w, h], radius=radius, fill=fill_color)
    temp_p = "temp_box_ui.png"
    rect_img.save(temp_p)
    return ImageClip(temp_p).set_ismask(False)

def get_styled_header(text, dur, W):
    """
    Headline/Hook box at the top. 
    Uses 'caption' method to wrap text automatically within the box.
    """
    box_w, box_h = W - 60, 200
    bg = create_rounded_box(box_w, box_h, (15, 25, 55), opacity=245)
    
    txt = TextClip(text.upper(), fontsize=42, color='yellow', font='Arial-Bold', 
                   size=(box_w-40, box_h-20), method='caption').set_position('center')
    
    return CompositeVideoClip([bg, txt], size=(box_w, box_h)).set_duration(dur)

def get_styled_ticker(text, dur, W, box_h):
    """
    FIXED: Subtitles scrolling synced with audio duration.
    Calculates speed as (Text Width + Box Width) / Duration.
    """
    box_w = W - 40
    bg = create_rounded_box(box_w, box_h, (120, 0, 0), opacity=255)
    
    # 'label' method is critical - it allows the clip to be wider than the screen
    txt = TextClip(text, fontsize=36, color='white', font='Arial-Bold', method='label').set_duration(dur)
    
    # The math for perfect sync:
    # We want the text to travel its own width + the screen width to fully clear the box.
    scroll_speed = (txt.w + box_w) / dur
    
    # Scrolling from Right to Left
    txt_scrolling = txt.set_position(lambda t: (box_w - (scroll_speed * t), 'center'))
    
    # Wrap in a CompositeVideoClip to apply the background and mask the text
    return CompositeVideoClip([bg, txt_scrolling], size=(box_w, box_h)).set_duration(dur)

def get_progress_bar(dur, W, H):
    """Creates a pulsing progress bar at the very bottom of the screen."""
    base = ColorClip(size=(W, 14), color=(30, 30, 30)).set_duration(dur).set_opacity(0.7)
    
    def make_frame(t):
        progress_w = max(1, int((t / dur) * W))
        # Pulsing intensity for a high-end feel
        pulse = 200 + int(55 * abs(0.5 - (t % 1)) * 2)
        return ColorClip(size=(progress_w, 14), color=(pulse, pulse, 0)).to_ImageClip().img
    
    bar = VideoClip(make_frame, duration=dur).set_position(('left', 'bottom'))
    return CompositeVideoClip([base, bar]).set_position(('center', H-14))