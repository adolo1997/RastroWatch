import httpx

from ...config import settings
from ...schemas import PriceResult
from .base import PriceSource, safe_float


class ApifySource(PriceSource):
    actor_setting = ""

    @property
    def actor_id(self) -> str:
        return getattr(settings, self.actor_setting, "")

    @property
    def configured(self) -> bool:
        return bool(settings.apify_token and self.actor_id)

    async def search(self, query: str) -> list[PriceResult]:
        if not self.configured:
            return []
        url = f"https://api.apify.com/v2/acts/{self.actor_id}/run-sync-get-dataset-items"
        params = {"token": settings.apify_token, "timeout": int(self.timeout)}
        payload = {"query": query, "search": query, "maxItems": 20}
        async with httpx.AsyncClient(timeout=self.timeout + 5) as client:
            response = await client.post(url, params=params, json=payload)
            response.raise_for_status()
            data = response.json()
        results = []
        for item in data[:20] if isinstance(data, list) else []:
            price = safe_float(item.get("price") or item.get("priceValue") or item.get("amount"))
            if price is None:
                continue
            results.append(PriceResult(source=self.name, title=item.get("title") or item.get("name") or query, price=price, currency=item.get("currency", "EUR"), condition=item.get("condition"), url=item.get("url"), image_url=item.get("image") or item.get("imageUrl"), sold=bool(item.get("sold", False)), location=item.get("location"), confidence=0.58, raw=item))
        return results
