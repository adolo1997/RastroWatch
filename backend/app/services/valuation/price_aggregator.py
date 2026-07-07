import asyncio
import logging
from collections.abc import Iterable

from ...schemas import PriceResult
from ..sources import all_sources

logger = logging.getLogger("rastrowatch.sources")


def source_status() -> dict[str, bool]:
    sources = {source.name: source.configured for source in all_sources()}
    return {
        "openai": False,
        "ebay": sources.get("eBay", False),
        "thewatchapi": sources.get("TheWatchAPI", False),
        "watchcharts": sources.get("WatchCharts", False),
        "wallapop_apify": sources.get("Wallapop Apify", False),
        "milanuncios_apify": sources.get("Milanuncios Apify", False),
        "catawiki_apify": sources.get("Catawiki Apify", False),
    }


class PriceAggregator:
    async def search(self, queries: Iterable[str], source_filters: list[str] | None = None) -> list[PriceResult]:
        normalized_filters = {f.lower() for f in source_filters or []}
        sources = [source for source in all_sources() if not normalized_filters or source.name.lower() in normalized_filters]
        tasks = [self._safe_search(source, query) for query in {q for q in queries if q.strip()} for source in sources]
        if not tasks:
            return []
        nested = await asyncio.gather(*tasks)
        deduped: dict[str, PriceResult] = {}
        for results in nested:
            for result in results:
                key = f"{result.source}|{result.url or result.title}|{result.price}"
                deduped[key] = result
        return list(deduped.values())

    async def _safe_search(self, source, query: str) -> list[PriceResult]:
        if not source.configured:
            logger.info("Fuente %s no configurada", source.name)
            return []
        try:
            return await asyncio.wait_for(source.search(query), timeout=source.timeout + 8)
        except Exception as exc:
            logger.warning("Fuente %s falló para %s: %s", source.name, query, exc)
            return [PriceResult(source=source.name, title="Fuente con error", price=0, currency="EUR", sold=False, confidence=0, raw={"error": str(exc), "query": query})]
