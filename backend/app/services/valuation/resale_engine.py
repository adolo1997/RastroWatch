def opportunity_from_price(price_seen: float | None, recommended_buy_price: float | None, median: float | None, high: float | None) -> tuple[str, str, list[str]]:
    warnings: list[str] = []
    if price_seen is None or recommended_buy_price is None or median is None or high is None:
        return "datos insuficientes", "investigar más", ["Datos insuficientes para comparar con el precio visto."]
    if price_seen <= recommended_buy_price * 0.75:
        warnings.append("Precio visto muy bajo: oportunidad potencial, pero revisa autenticidad, averías y procedencia.")
        return "muy buena", "comprar", warnings
    if price_seen <= recommended_buy_price:
        return "buena", "comprar", warnings
    if price_seen <= median:
        return "normal", "negociar", warnings
    if price_seen > high:
        return "mala", "evitar", warnings
    return "caro", "negociar", warnings
