"""Ollama LLM service for transcript analysis and highlight extraction."""

import json
import logging
from dataclasses import dataclass
from typing import Sequence

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class TranscriptSegmentDTO:
    segment_id: int
    text: str


@dataclass
class HighlightMomentDTO:
    start_segment_id: int
    end_segment_id: int
    suggested_duration_seconds: float | None = None
    engagement_reason: str | None = None
    engagement_score: float | None = None


class OllamaAnalysisService:
    """Service untuk analisis transkrip menggunakan Ollama LLM."""

    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.default_ollama_model
        self.base_url = settings.ollama_base_url.rstrip("/")

    def _build_prompt(self, segments: Sequence[TranscriptSegmentDTO]) -> str:
        segment_lines = "\n".join(
            f"[{s.segment_id}] {s.text}" for s in segments
        )
        return f"""You are a viral video content analyst. Given the transcript
segments below, identify the top 3 most engaging moments.

Rules:
- Output ONLY valid JSON. No markdown, no explanation.
- Return an object with a "moments" array.
- Each moment must have: start_segment_id, end_segment_id,
  suggested_duration_seconds, engagement_reason, engagement_score
  (0.0 to 1.0).
- start_segment_id and end_segment_id MUST be valid segment IDs
  from the input.
- Keep segments contiguous when possible.
- engagement_score should reflect likelihood to retain viewers.

Transcript segments:
{segment_lines}

Output format example:
{{
  "moments": [
    {{
      "start_segment_id": 5,
      "end_segment_id": 7,
      "suggested_duration_seconds": 15.0,
      "engagement_reason": "Contains a surprising statistic.",
      "engagement_score": 0.92
    }}
  ]
}}"""

    async def analyze(self, segments: Sequence[TranscriptSegmentDTO]) -> list[HighlightMomentDTO]:
        """Send transcript to Ollama and parse highlight moments."""
        prompt = self._build_prompt(segments)
        logger.info("Sending analysis request to Ollama model=%s", self.model_name)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.2},
                },
            )
            response.raise_for_status()
            payload = response.json()

        raw_text = payload.get("response", "")
        moments = self._parse_response(raw_text, segments)
        logger.info("Analysis complete: extracted %d moments", len(moments))
        return moments

    def _parse_response(
        self, raw_text: str, valid_segments: Sequence[TranscriptSegmentDTO]
    ) -> list[HighlightMomentDTO]:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON from LLM: {exc}") from exc

        raw_moments = data.get("moments", [])
        if not isinstance(raw_moments, list):
            raise ValueError("LLM response missing 'moments' array.")

        valid_ids = {s.segment_id for s in valid_segments}
        moments: list[HighlightMomentDTO] = []

        for item in raw_moments[:5]:
            start_id = item.get("start_segment_id")
            end_id = item.get("end_segment_id")
            if start_id not in valid_ids or end_id not in valid_ids:
                logger.warning("Skipping invalid segment IDs: %s-%s", start_id, end_id)
                continue

            moments.append(
                HighlightMomentDTO(
                    start_segment_id=start_id,
                    end_segment_id=end_id,
                    suggested_duration_seconds=item.get("suggested_duration_seconds"),
                    engagement_reason=item.get("engagement_reason"),
                    engagement_score=item.get("engagement_score"),
                )
            )

        return moments


ollama_service = OllamaAnalysisService()
