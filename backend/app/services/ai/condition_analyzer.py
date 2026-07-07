def normalize_condition(value: str | None) -> str:
    normalized = (value or "desconocido").strip().lower()
    aliases = {
        "poor": "malo",
        "fair": "usado",
        "used": "usado",
        "good": "bueno",
        "excellent": "excelente",
        "untested": "sin probar",
        "unknown": "desconocido",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in {"malo", "usado", "bueno", "excelente", "sin probar", "desconocido"}:
        return "desconocido"
    return normalized
