"""Pipeline FFmpeg/MoviePy untuk rendering klip."""

import logging
from pathlib import Path
from typing import Sequence

from moviepy import (
    CompositeVideoClip,
    VideoFileClip,
)

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RenderingService:
    """Service untuk rendering klip vertikal dengan subtitle dan b-roll."""

    def __init__(self) -> None:
        settings = get_settings()
        self.assets_root = settings.assets_root

    def render_clip(
        self,
        source_path: str | Path,
        output_path: str | Path,
        start: float,
        end: float,
        aspect_ratio: str = "9:16",
        subtitle_words: Sequence[tuple[str, float, float]] | None = None,
        broll_paths: Sequence[str | Path] | None = None,
        broll_timings: Sequence[tuple[float, float]] | None = None,
    ) -> dict:
        """Render klip dari video sumber.

        Args:
            source_path: Path ke video sumber.
            output_path: Path output untuk klip yang dirender.
            start: Waktu mulai dalam detik.
            end: Waktu selesai dalam detik.
            aspect_ratio: Rasio aspek output ('9:16', '16:9', dll).
            subtitle_words: Daftar tuple (word, start, end) untuk subtitle.
            broll_paths: Path ke asset b-roll.
            broll_timings: Daftar tuple (start, end) untuk setiap b-roll.

        Returns:
            dict dengan metadata rendering.
        """
        source_path = Path(source_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Rendering clip: source=%s output=%s start=%.2f end=%.2f",
            source_path,
            output_path,
            start,
            end,
        )

        try:
            with VideoFileClip(str(source_path)) as video:
                duration = video.duration or 0
                safe_end = min(end, duration)
                if safe_end <= start:
                    raise ValueError(f"Invalid time range: {start}-{safe_end}")

                clip = video.subclipped(start, safe_end)
                target_width, target_height = self._resolve_dimensions(aspect_ratio)
                clip = self._crop_to_aspect(clip, target_width, target_height)

                layers: list = [clip]

                if broll_paths and broll_timings:
                    broll_layers = self._build_broll_layers(
                        clip.duration, broll_paths, broll_timings
                    )
                    layers.extend(broll_layers)

                if subtitle_words:
                    subtitle_layer = self._build_subtitle_layer(
                        clip.duration, clip.size[0], subtitle_words
                    )
                    if subtitle_layer is not None:
                        layers.append(subtitle_layer)

                final = CompositeVideoClip(layers, size=clip.size)
                final.audio = clip.audio

                final.write_videofile(
                    str(output_path),
                    codec="libx264",
                    audio_codec="aac",
                    fps=clip.fps or 24,
                    preset="fast",
                    threads=4,
                    logger=None,
                )

                metadata = {
                    "output_path": str(output_path),
                    "resolution": f"{final.w}x{final.h}",
                    "duration_seconds": float(final.duration or 0),
                }

                logger.info("Render selesai: %s", metadata)
                return metadata

        except Exception as exc:
            logger.error("Render gagal: %s", exc, exc_info=True)
            raise RuntimeError(f"Gagal rendering klip: {exc}") from exc

    def _resolve_dimensions(self, aspect_ratio: str) -> tuple[int, int]:
        mapping = {
            "9:16": (1080, 1920),
            "16:9": (1920, 1080),
            "4:5": (1080, 1350),
            "1:1": (1080, 1080),
        }
        if aspect_ratio not in mapping:
            raise ValueError(f"Aspect ratio tidak didukung: {aspect_ratio}")
        return mapping[aspect_ratio]

    def _crop_to_aspect(self, clip, width: int, height: int):
        original_w, original_h = clip.size
        target_aspect = width / height
        original_aspect = original_w / original_h

        if abs(original_aspect - target_aspect) < 0.01:
            return clip.resized(new_size=(width, height))

        if original_aspect > target_aspect:
            new_w = int(original_h * target_aspect)
            x1 = (original_w - new_w) // 2
            x2 = x1 + new_w
            return clip.cropped(x1=x1, y1=0, x2=x2, y2=original_h).resized(
                new_size=(width, height)
            )

        new_h = int(original_w / target_aspect)
        y1 = (original_h - new_h) // 2
        y2 = y1 + new_h
        return clip.cropped(x1=0, y1=y1, x2=original_w, y2=y2).resized(
            new_size=(width, height)
        )

    def _build_broll_layers(
        self,
        clip_duration: float,
        broll_paths: Sequence[str | Path],
        broll_timings: Sequence[tuple[float, float]],
    ) -> list:
        layers = []
        for broll_path, (start, end) in zip(broll_paths, broll_timings):
            if not broll_path or not Path(broll_path).exists():
                continue
            try:
                broll = VideoFileClip(str(broll_path))
                broll = broll.resized(new_size=(int(broll.w * 0.35), int(broll.h * 0.35)))
                broll = broll.with_start(start)
                broll = broll.with_end(min(end, clip_duration))
                broll = broll.with_position(("right", "bottom"))
                layers.append(broll)
            except Exception as exc:
                logger.warning("Gagal memuat b-roll %s: %s", broll_path, exc)
        return layers

    def _build_subtitle_layer(
        self,
        clip_duration: float,
        width: int,
        subtitle_words: Sequence[tuple[str, float, float]],
    ) -> object | None:
        try:
            from moviepy import TextClip

            height = 1920
            clips = []
            for word, start, end in subtitle_words:
                if end <= start or end > clip_duration:
                    continue
                txt = TextClip(
                    text=word.upper(),
                    font_size=int(width * 0.045),
                    font="Arial-Bold",
                    color="white",
                    stroke_color="black",
                    stroke_width=2,
                    method="caption",
                    size=(int(width * 0.9), None),
                )
                txt = txt.with_start(start).with_end(end)
                txt = txt.with_position(("center", int(height * 0.85)))
                clips.append(txt)

            if not clips:
                return None

            return CompositeVideoClip(clips, size=(width, height))
        except Exception as exc:
            logger.warning("Gagal membuat subtitle layer: %s", exc)
            return None


rendering_service = RenderingService()
