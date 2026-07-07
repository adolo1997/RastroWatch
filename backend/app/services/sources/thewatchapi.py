from ...config import settings
from ...schemas import PriceResult
from .base import PriceSource, get_json, safe_float


class TheWatchApiSource(PriceSource):
    name = "TheWatchAPI"

    @property
    def configured(self) -> bool:
        return bool(settings.thewatchapi_key)

    async def search(self, query: str) -> list[PriceResult]:
        if not self.configured:
            return []
        data = await get_json("https://api.thewatchapi.com/v1/search", headers={"Authorization": f"Bearer {settings.thewatchapi_key}"}, params={"q": query}, timeout=self.timeout)
        items = data.get("results", data.get("data", []))
        results = []
        for item in items[:20]:
            price = safe_float(item.get("price") or item.get("market_price"))
            if price is None:
                continue
            results.append(PriceResult(source=self.name, title=item.get("name") or item.get("title") or query, brand=item.get("brand"), model=item.get("model"), reference=item.get("reference"), price=price, currency=item.get("currency", "EUR"), condition=item.get("condition"), url=item.get("url"), image_url=item.get("image_url"), sold=False, confidence=0.7, raw=item))
        return results
