from ast import main
from datetime import datetime
import re
from typing import Optional, List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    ForeignKey,
    select,
)

from models.base import Base
import models.grade
import models.ascent
import models.crag
import models.similarity


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

    sector_slug: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sector_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    crag_slug: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    crag_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Scraping status
    scraped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=datetime.now()
    )
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

    # Similarity matrix ID (for future use)
    similarity_matrix_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Main boulder flag and reference for duplicate boulders
    main_boulder_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Foreign Keys
    grade_id: Mapped[int] = mapped_column(ForeignKey("grade.id"), index=True)
    crag_id: Mapped[int] = mapped_column(ForeignKey("crag.id"), index=True)

    # Relationship to other entities via Foreign Keys
    grade: Mapped["models.grade.Grade"] = relationship(
        "Grade", back_populates="boulders", foreign_keys=[grade_id]
    )
    crag: Mapped["models.crag.Crag"] = relationship(
        "Crag", back_populates="boulders"
    )

    # Association object for ascents
    ascents: Mapped[List["models.ascent.Ascent"]] = relationship(
        "Ascent", back_populates="boulder"
    )

    # Similarity relationships
    similarities_as_id1: Mapped[List["models.similarity.Similarity"]] = (
        relationship(
            "Similarity", foreign_keys="[Similarity.id1]", viewonly=True
        )
    )
    similarities_as_id2: Mapped[List["models.similarity.Similarity"]] = (
        relationship(
            "Similarity", foreign_keys="[Similarity.id2]", viewonly=True
        )
    )

    def __repr__(self):
        return f"<Boulder(name: {self.name}, grade: {self.grade.value}, Ascents: {len(self.ascents)})>"

    @classmethod
    def get_by_slug(cls, db_session, slug: str):
        """Retrieve a Boulder by its slug."""
        return db_session.scalar(select(cls).where(cls.slug == slug))

    def mark_as_scraped(self, db):
        self.scraped_ascents_at = datetime.now()
        self.ascent_scrape_error = None
        self.ascent_retry_count = 0
        db.add(self)
        db.commit()
        db.refresh(self)
        return self

    def update_last_ascent_scrape_attempt(self, db):
        self.last_ascent_scrape_attempt = datetime.now()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self
