import os
from moviepy.editor import *
import moviepy.video.fx.all as vfx


def apply_speed_multiplier(clip, factor=1.1):
    return clip.fx(vfx.speedx, factor)


def apply_ken_burns(clip, zoom_ratio=0.04):
    return clip.fx(vfx.resize, lambda t: 1.0 + (zoom_ratio * t))


def create_sentence_scrolling(full_text, duration, W, H):

    sentences = (
        full_text.replace("!", ".")
        .replace("?", ".")
        .split(".")
    )

    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

    if not sentences:
        return TextClip(
            full_text,
            fontsize=60,
            color="white",
            font="Arial-Bold",
            method="caption",
            size=(W - 200, None),
            align="center",
            stroke_color="black",
            stroke_width=2
        ).set_duration(duration).set_position(("center", 1100))

    each_dur = duration / len(sentences)
    clips = []

    for i, sentence in enumerate(sentences):

        txt = TextClip(
            sentence,
            fontsize=65,
            color="white",
            font="Arial-Bold",
            method="caption",
            size=(W - 200, None),
            align="center",
            stroke_color="black",
            stroke_width=2
        ).set_start(i * each_dur).set_duration(each_dur)

        txt = txt.set_position(lambda t: ("center", 1150 - (t * 20)))

        clips.append(txt)

    return CompositeVideoClip(clips, size=(W, H))


def add_background_audio(video_clip, bgm_path, volume=0.12):

    if os.path.exists(bgm_path):

        bgm = (
            AudioFileClip(bgm_path)
            .volumex(volume)
            .set_duration(video_clip.duration)
        )

        if video_clip.audio:
            final_audio = CompositeAudioClip([video_clip.audio, bgm])
            return video_clip.set_audio(final_audio)

    return video_clip
