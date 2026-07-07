import base64
import json
from pathlib import Path

import httpx

from ...config import settings
from ...schemas import AIWatchAnalysis
from .condition_analyzer import normalize_condition
from .prompt_builder import build_watch_identifier_prompt


def fallback_analysis(reason: str = "Identificación IA no configurada") -> AIWatchAnalysis:
    return AIWatchAnalysis(
        detected_condition="desconocido",
        visible_damage=[],
        authenticity_risk="desconocido",
        confidence=0.0,
        search_queries=[],
        notes=reason,
    )


class WatchIdentifier:
    def __init__(self, timeout: float = 35.0):
        self.timeout = timeout

    async def identify(self, image_path: str) -> AIWatchAnalysis:
        if not settings.openai_api_key:
            return fallback_analysis("OpenAI API key no configurada; identificación IA desactivada.")

        path = Path(image_path)
        if not path.exists():
            return fallback_analysis("Imagen no encontrada para analizar.")

        model = settings.openai_model or settings.default_openai_vision_model
        image_b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
        mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
        payload = {
            "model": model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": build_watch_identifier_prompt()},
                        {"type": "input_image", "image_url": f"data:{mime};base64,{image_b64}"},
                    ],
                }
            ],
            "text": {"format": {"type": "json_object"}},
        }
        headers = {"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post("https://api.openai.com/v1/responses", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            return fallback_analysis(f"Error al consultar OpenAI Vision: {exc}")

        text = self._extract_text(data)
        try:
            parsed = json.loads(text)
        except Exception:
            return fallback_analysis("OpenAI no devolvió JSON válido; análisis guardado como pendiente.")

        parsed["detected_condition"] = normalize_condition(parsed.get("detected_condition"))
        parsed.setdefault("visible_damage", [])
        parsed.setdefault("search_queries", [])
        parsed.setdefault("confidence", 0.0)
        parsed.setdefault("authenticity_risk", "desconocido")
        return AIWatchAnalysis(**parsed)

    def _extract_text(self, data: dict) -> str:
        if data.get("output_text"):
            return data["output_text"]
        chunks: list[str] = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"}:
                    chunks.append(content.get("text", ""))
        return "".join(chunks)
