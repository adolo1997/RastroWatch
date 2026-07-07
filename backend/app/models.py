from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship
from .database import Base


class Watch(Base):
    __tablename__ = "watches"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(120), default="")
    model = Column(String(160), default="")
    reference = Column(String(120), default="")
    movement_type = Column(String(40), default="desconocido")
    diameter = Column(Float, nullable=True)
    approximate_year = Column(Integer, nullable=True)
    condition = Column(String(40), default="usado")
    estimated_min_price = Column(Float, nullable=True)
    estimated_avg_price = Column(Float, nullable=True)
    estimated_max_price = Column(Float, nullable=True)
    recommended_buy_price = Column(Float, nullable=True)
    seen_price = Column(Float, nullable=True)
    resale_margin = Column(Float, nullable=True)
    counterfeit_risk = Column(String(20), default="medio")
    price_reliability = Column(String(20), default="media")
    identification_notes = Column(Text, default="")
    prebuy_checklist = Column(Text, default="")
    price_sources = Column(Text, default="")
    location = Column(String(60), default="otro")
    quick_notes = Column(Text, default="")
    status = Column(String(40), default="investigado")
    opportunity = Column(String(40), default="normal")
    recommendation = Column(String(40), default="investigar más")
    valuation_warning = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    images = relationship("WatchImage", back_populates="watch", cascade="all, delete-orphan")


class WatchImage(Base):
    __tablename__ = "watch_images"

    id = Column(Integer, primary_key=True, index=True)
    watch_id = Column(Integer, ForeignKey("watches.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    watch = relationship("Watch", back_populates="images")
