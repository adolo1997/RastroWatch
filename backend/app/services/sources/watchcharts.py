from ...config import settings
from ...schemas import PriceResult
from .base import PriceSource, get_json, safe_float


class WatchChartsSource(PriceSource):
    name = "WatchCharts"

    @property
    def configured(self) -> bool:
        return bool(settings.watchcharts_api_key)

    async def search(self, query: str) -> list[PriceResult]:
        if not self.configured:
            return []
        data = await get_json("https://api.watchcharts.com/v1/search", headers={"Authorization": f"Bearer {settings.watchcharts_api_key}"}, params={"q": query}, timeout=self.timeout)
        items = data.get("results", data.get("data", []))
        results = []
        for item in items[:20]:
            price = safe_float(item.get("market_price") or item.get("price"))
            if price is None:
                continue
            results.append(PriceResult(source=self.name, title=item.get("title") or item.get("name") or query, brand=item.get("brand"), model=item.get("model"), reference=item.get("reference"), price=price, currency=item.get("currency", "EUR"), condition=item.get("condition"), url=item.get("url"), image_url=item.get("image_url"), sold=True, confidence=0.78, raw=item))
        return results
