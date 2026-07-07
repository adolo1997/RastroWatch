import json


def build_watch_identifier_prompt() -> str:
    schema = {
        "brand": "string|null",
        "model": "string|null",
        "reference": "string|null",
        "movement": "cuarzo|automático|mecánico|solar|desconocido|null",
        "approximate_year": "string|null",
        "case_material": "string|null",
        "dial_color": "string|null",
        "detected_condition": "malo|usado|bueno|excelente|sin probar|desconocido",
        "visible_damage": ["string"],
        "authenticity_risk": "bajo|medio|alto|desconocido",
        "confidence": 0.0,
        "search_queries": ["string"],
        "notes": "string",
    }
    return (
        "Analiza la imagen de un reloj de segunda mano para una app privada de tasación. "
        "Devuelve solo JSON estricto, sin markdown. No inventes seguridad absoluta: si algo no está claro usa null, "
        "desconocido y baja confianza. Identifica marca probable, modelo probable, referencia si se ve o puede inferirse, "
        "tipo/movimiento probable, estado visual, daños visibles, señales de falso/modificado/sospechoso, qué revisar manualmente "
        "y queries útiles para buscar precios actuales. Esquema exacto: " + json.dumps(schema, ensure_ascii=False)
    )
