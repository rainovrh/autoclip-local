"""Wrapper faster-whisper untuk transkripsi word-level."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from faster_whisper import WhisperModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class WordTimestamp:
    word: str
    start: float
    end: float
    probability: float | None = None


@dataclass
class SegmentResult:
    index: int
    start: float
    end: float
    text: str
    words: Sequence[WordTimestamp]


@dataclass
class TranscriptionResult:
    text: str
    language: str | None
    segments: Sequence[SegmentResult]


class WhisperTranscriptionService:
    """Service untuk transkripsi audio/video menggunakan faster-whisper."""

    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.default_whisper_model
        self._model: WhisperModel | None = None

    def _load_model(self) -> WhisperModel:
        if self._model is None:
            logger.info("Loading Whisper model: %s", self.model_name)
            self._model = WhisperModel(
                self.model_name,
                device="cpu",
                compute_type="int8",
            )
        return self._model

    def transcribe(self, file_path: Path) -> TranscriptionResult:
        """Transkripsi file audio/video dan kembalikan hasil dengan word-level timestamps."""
        model = self._load_model()
        logger.info("Transcribing: %s", file_path)

        segments_generator, info = model.transcribe(
            str(file_path),
            language=None,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        segments: list[SegmentResult] = []
        full_text_parts: list[str] = []

        for seg_idx, segment in enumerate(segments_generator):
            seg_text = segment.text.strip()
            full_text_parts.append(seg_text)

            words: list[WordTimestamp] = []
            if segment.words is not None:
                for word_idx, word in enumerate(segment.words):
                    words.append(
                        WordTimestamp(
                            word=word.word.strip(),
                            start=word.start,
                            end=word.end,
                            probability=word.probability,
                        )
                    )

            segments.append(
                SegmentResult(
                    index=seg_idx,
                    start=segment.start,
                    end=segment.end,
                    text=seg_text,
                    words=words,
                )
            )

        language = info.language if info else None
        logger.info(
            "Transcription complete: %s segments, language=%s",
            len(segments),
            language,
        )
        return TranscriptionResult(
            text=" ".join(full_text_parts).strip(),
            language=language,
            segments=segments,
        )

    def unload(self) -> None:
        if self._model is not None:
            del self._model
            self._model = None


whisper_service = WhisperTranscriptionService()
