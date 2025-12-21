from datetime import datetime, date
from typing import Optional, List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    ForeignKey,
)

from models.base import Base
import models.grade
import models.ascent
import models.sector


class Boulder(Base):
    __tablename__ = "boulder"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    external_db_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String)
    name_normalized: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String)

    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    category: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # e.g., 1 for Boulder, 0 for Route
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Scraping status
    scraped_ascents: Mapped[bool] = mapped_column(Boolean, default=False)
    scraped_ascents_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    last_ascent_scrape_attempt: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    ascent_scrape_error: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )
    ascent_retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Foreign Keys
    grade_id: Mapped[int] = mapped_column(ForeignKey("grade.id"))
    sector_id: Mapped[int] = mapped_column(ForeignKey("sector.id"))

    # Relationship to other entities via Foreign Keys
    grade: Mapped["models.grade.Grade"] = relationship(
        "Grade", back_populates="boulders", foreign_keys=[grade_id]
    )
    sector: Mapped["models.sector.Sector"] = relationship(
        "Sector", back_populates="boulders"
    )

    # Association object for ascents
    ascents: Mapped[List["models.ascent.Ascent"]] = relationship(
        "Ascent", back_populates="boulder"
    )

    def __repr__(self):
        return f"<Boulder(name: {self.name}, grade: {self.grade.value}, setters: {self.setters}, Ascents: {self.ascents})"
