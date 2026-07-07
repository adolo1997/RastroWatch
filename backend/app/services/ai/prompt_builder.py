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
        "market_value_initial_estimate": "number|null",
        "current_real_value_estimate_low": "number|null",
        "current_real_value_estimate_median": "number|null",
        "current_real_value_estimate_high": "number|null",
        "recommended_buy_price": "number|null",
        "probable_sale_value": "number|null",
        "resale_margin": "number|null",
        "recommendation": "comprar|negociar|investigar más|evitar|null",
        "warnings": ["string"],
        "confidence": 0.0,
        "search_queries": ["string"],
        "notes": "string",
    }
    return (
        "Analiza la imagen de un reloj de segunda mano para una app privada de tasación. "
        "Devuelve solo JSON estricto, sin markdown. No inventes seguridad absoluta: si algo no está claro usa null, "
        "desconocido y baja confianza. Identifica marca probable, modelo probable, referencia si se ve o puede inferirse, "
        "tipo/movimiento probable, estado visual, daños visibles, señales de falso/modificado/sospechoso, qué revisar manualmente "
        "valor inicial aproximado, valor real actual bajo/medio/alto, compra recomendada, venta probable, margen estimado "
        "y queries útiles para validar después en eBay, Wallapop, TodoColección y Google. "
        "No inventes precios: si la imagen no permite una estimación razonable devuelve null y explica datos insuficientes. "
        "Incluye siempre confidence y warnings. Esquema exacto: " + json.dumps(schema, ensure_ascii=False)
    )
