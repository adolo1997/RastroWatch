import base64

import httpx

from ...config import settings
from ...schemas import PriceResult
from .base import PriceSource, safe_float


class EbaySource(PriceSource):
    name = "eBay"

    @property
    def configured(self) -> bool:
        return bool(settings.ebay_client_id and settings.ebay_client_secret)

    async def _token(self) -> str:
        credentials = base64.b64encode(f"{settings.ebay_client_id}:{settings.ebay_client_secret}".encode()).decode()
        headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post("https://api.ebay.com/identity/v1/oauth2/token", headers=headers, data=data)
            response.raise_for_status()
            return response.json()["access_token"]

    async def search(self, query: str) -> list[PriceResult]:
        if not self.configured:
            return []
        token = await self._token()
        headers = {"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": settings.ebay_marketplace}
        params = {"q": query, "category_ids": "31387", "limit": "20"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get("https://api.ebay.com/buy/browse/v1/item_summary/search", headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
        results = []
        for item in data.get("itemSummaries", []):
            price = safe_float((item.get("price") or {}).get("value"))
            if price is None:
                continue
            results.append(PriceResult(source=self.name, title=item.get("title", ""), price=price, currency=(item.get("price") or {}).get("currency", "EUR"), condition=item.get("condition"), url=item.get("itemWebUrl"), image_url=(item.get("image") or {}).get("imageUrl"), sold=False, location=(item.get("itemLocation") or {}).get("country"), confidence=0.65, raw=item))
        return results
