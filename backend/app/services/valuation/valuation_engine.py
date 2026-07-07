from statistics import median

from ...schemas import AIWatchAnalysis, PriceResult, ValuationResult
from .confidence_engine import overall_confidence, result_similarity_score
from .resale_engine import opportunity_from_price


CONDITION_FACTORS = {"excelente": 1.10, "bueno": 1.0, "usado": 0.85, "malo": 0.65, "sin probar": 0.55, "desconocido": 0.85}


class ValuationEngine:
    def calculate(self, results: list[PriceResult], analysis: AIWatchAnalysis | None = None, price_seen: float | None = None) -> ValuationResult:
        warnings: list[str] = []
        normalized = []
        for result in results:
            if result.price and result.price > 0:
                result.confidence = result_similarity_score(result, analysis)
                normalized.append(result)
        normalized.sort(key=lambda r: (not r.sold, -r.confidence, r.price))

        prices = [r.price for r in normalized]
        if len(prices) > 6:
            q1_index = len(prices) // 4
            q3_index = (len(prices) * 3) // 4
            sorted_prices = sorted(prices)
            iqr = sorted_prices[q3_index] - sorted_prices[q1_index]
            low_bound = sorted_prices[q1_index] - 1.5 * iqr
            high_bound = sorted_prices[q3_index] + 1.5 * iqr
            normalized = [r for r in normalized if low_bound <= r.price <= high_bound]
            prices = [r.price for r in normalized]

        if not prices:
            return ValuationResult(opportunity="datos insuficientes", recommendation="investigar más", warnings=["Datos insuficientes: no hay precios fiables configurados o encontrados."], sources_used=sorted({r.source for r in results}), confidence=overall_confidence([], analysis), results=results)

        condition = (analysis.detected_condition if analysis else "desconocido") or "desconocido"
        factor = CONDITION_FACTORS.get(condition, 0.85)
        low = min(prices) * factor
        med = median(prices) * factor
        high = max(prices) * factor
        recommended = med * 0.65
        probable_sale = med * 0.90
        resale_margin = (probable_sale - price_seen) if price_seen is not None else (probable_sale - recommended)
        opportunity, recommendation, price_warnings = opportunity_from_price(price_seen, recommended, med, high)
        warnings.extend(price_warnings)

        if analysis and analysis.authenticity_risk == "alto":
            warnings.append("Riesgo alto de falsificación: validar calibre, documentación, número de serie y vendedor antes de comprar.")
            recommendation = "evitar" if opportunity in {"mala", "caro"} else "investigar más"
        if len(normalized) < 3:
            warnings.append("Pocas fuentes fiables: valoración aproximada con datos limitados.")

        return ValuationResult(
            market_value_initial=round(median(prices), 2),
            current_real_value_low=round(low, 2),
            current_real_value_median=round(med, 2),
            current_real_value_high=round(high, 2),
            recommended_buy_price=round(recommended, 2),
            probable_sale_value=round(probable_sale, 2),
            resale_margin=round(resale_margin, 2),
            opportunity=opportunity,
            recommendation=recommendation,
            warnings=warnings,
            sources_used=sorted({r.source for r in normalized}),
            confidence=overall_confidence(normalized, analysis),
            results=normalized,
        )
