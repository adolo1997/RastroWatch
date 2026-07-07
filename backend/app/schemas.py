from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WatchImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    original_name: str | None = ""
    url: str


class WatchBase(BaseModel):
    brand: str | None = ""
    model: str | None = ""
    reference: str | None = ""
    movement_type: str | None = "desconocido"
    diameter: float | None = None
    approximate_year: int | None = None
    condition: str | None = "usado"
    estimated_min_price: float | None = None
    estimated_avg_price: float | None = None
    estimated_max_price: float | None = None
    recommended_buy_price: float | None = None
    seen_price: float | None = None
    resale_margin: float | None = None
    counterfeit_risk: str | None = "medio"
    price_reliability: str | None = "media"
    identification_notes: str | None = ""
    prebuy_checklist: str | None = ""
    price_sources: str | None = ""
    location: str | None = "otro"
    quick_notes: str | None = ""
    status: str | None = "investigado"


class WatchCreate(WatchBase):
    pass


class WatchUpdate(WatchBase):
    pass


class WatchOut(WatchBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    opportunity: str
    recommendation: str
    valuation_warning: str | None = ""
    images: list[WatchImageOut] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LoginIn(BaseModel):
    username: str
    password: str


class AiStubOut(BaseModel):
    message: str
    ready: bool = False
