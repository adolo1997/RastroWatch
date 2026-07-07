from ...schemas import AIWatchAnalysis, PriceResult


def result_similarity_score(result: PriceResult, analysis: AIWatchAnalysis | None) -> float:
    if not analysis:
        return result.confidence
    haystack = " ".join(filter(None, [result.title, result.brand, result.model, result.reference])).lower()
    score = result.confidence
    for value, boost in [(analysis.brand, 0.08), (analysis.model, 0.08), (analysis.reference, 0.12)]:
        if value and value.lower() in haystack:
            score += boost
    return min(score, 1.0)


def overall_confidence(results: list[PriceResult], analysis: AIWatchAnalysis | None) -> float:
    if not results:
        return min((analysis.confidence if analysis else 0.0), 0.25)
    usable = [r.confidence for r in results if r.price > 0]
    base = sum(usable) / len(usable) if usable else 0.0
    ai = analysis.confidence if analysis else 0.0
    return round(min((base * 0.7) + (ai * 0.3), 1.0), 2)
