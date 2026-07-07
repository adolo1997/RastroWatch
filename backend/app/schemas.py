from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


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


class AIWatchAnalysis(BaseModel):
    brand: str | None = None
    model: str | None = None
    reference: str | None = None
    movement: str | None = None
    approximate_year: str | None = None
    case_material: str | None = None
    dial_color: str | None = None
    detected_condition: str = "desconocido"
    visible_damage: list[str] = Field(default_factory=list)
    authenticity_risk: str = "desconocido"
    confidence: float = 0.0
    search_queries: list[str] = Field(default_factory=list)
    notes: str = ""


class PriceResult(BaseModel):
    source: str
    title: str
    brand: str | None = None
    model: str | None = None
    reference: str | None = None
    price: float
    currency: str = "EUR"
    condition: str | None = None
    url: str | None = None
    image_url: str | None = None
    sold: bool = False
    location: str | None = None
    confidence: float = 0.0
    raw: dict[str, Any] = Field(default_factory=dict)


class ValuationResult(BaseModel):
    market_value_initial: float | None = None
    current_real_value_low: float | None = None
    current_real_value_median: float | None = None
    current_real_value_high: float | None = None
    recommended_buy_price: float | None = None
    probable_sale_value: float | None = None
    resale_margin: float | None = None
    opportunity: str = "datos insuficientes"
    recommendation: str = "investigar más"
    warnings: list[str] = Field(default_factory=list)
    sources_used: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    results: list[PriceResult] = Field(default_factory=list)


class PriceSearchIn(BaseModel):
    query: str
    price_seen: float | None = None
    source_filters: list[str] | None = None


class PriceSearchOut(BaseModel):
    results: list[PriceResult]
    valuation: ValuationResult


class WatchInvestigationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime | None = None
    uploaded_image_path: str
    uploaded_image_url: str | None = None
    user_price_seen: float | None = None
    user_location_seen: str | None = None
    user_notes: str | None = None
    ai_analysis: AIWatchAnalysis | None = None
    valuation_result: ValuationResult | None = None
    selected_brand: str | None = None
    selected_model: str | None = None
    selected_reference: str | None = None
    final_status: Literal["pendiente", "validado", "descartado", "comprado", "vendido"] = "pendiente"
    manual_corrections: dict[str, Any] = Field(default_factory=dict)


class WatchInvestigationPatch(BaseModel):
    selected_brand: str | None = None
    selected_model: str | None = None
    selected_reference: str | None = None
    final_status: str | None = None
    manual_corrections: dict[str, Any] | None = None
    user_price_seen: float | None = None
    user_location_seen: str | None = None
    user_notes: str | None = None
