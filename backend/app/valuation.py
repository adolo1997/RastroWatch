def calculate_valuation(watch: dict) -> dict:
    seen = watch.get("seen_price")
    min_price = watch.get("estimated_min_price")
    avg_price = watch.get("estimated_avg_price")
    max_price = watch.get("estimated_max_price")
    condition = (watch.get("condition") or "").lower()
    risk = (watch.get("counterfeit_risk") or "").lower()

    opportunity = "normal"
    recommendation = "investigar más"
    warning = ""

    if seen is not None and min_price is not None and avg_price is not None and max_price is not None:
        if seen < min_price:
            opportunity = "muy buena"
            recommendation = "comprar"
        elif min_price <= seen <= avg_price:
            opportunity = "buena"
            recommendation = "comprar"
        elif avg_price < seen <= max_price:
            opportunity = "normal"
            recommendation = "negociar"
        else:
            opportunity = "mala"
            recommendation = "evitar"

    if seen is not None and max_price is not None:
        margin = max(max_price - seen, 0)
    else:
        margin = watch.get("resale_margin")

    if condition == "sin probar":
        downgrade = {"muy buena": "buena", "buena": "normal", "normal": "mala", "mala": "mala"}
        opportunity = downgrade.get(opportunity, opportunity)
        if recommendation == "comprar":
            recommendation = "negociar"
        warning = "Reloj sin probar: reduce la valoración y revisa funcionamiento antes de comprar."

    if risk == "alto":
        recommendation = "investigar más" if recommendation != "evitar" else recommendation
        warning = (warning + " " if warning else "") + "Advertencia fuerte: riesgo alto de falsificación. Verifica documentación, calibre y vendedor."

    return {"opportunity": opportunity, "resale_margin": margin, "recommendation": recommendation, "valuation_warning": warning}
