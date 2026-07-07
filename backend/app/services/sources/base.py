from abc import ABC, abstractmethod
from typing import Any

import httpx

from ...schemas import PriceResult


class PriceSource(ABC):
    name: str

    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout

    @property
    @abstractmethod
    def configured(self) -> bool: ...

    @abstractmethod
    async def search(self, query: str) -> list[PriceResult]: ...

    def unavailable_result(self) -> PriceResult:
        return PriceResult(source=self.name, title="Fuente no configurada", price=0, currency="EUR", sold=False, confidence=0, raw={"status": "No configurada"})


def safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(str(value).replace("€", "").replace(",", ".").strip())
    except Exception:
        return None


async def get_json(url: str, *, headers: dict | None = None, params: dict | None = None, timeout: float = 12.0) -> dict:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
