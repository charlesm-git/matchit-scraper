from calendar import c
from datetime import date, datetime
from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    Boolean,
    Date,
    Date,
    DateTime,
    ForeignKey,
    String,
    Integer,
    select,
)

from models.base import Base
import models.country
import models.crag


class Area(Base):
    __tablename__ = "area"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String)
    name_normalized: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    external_db_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Foreign Key
    country_id: Mapped[int] = mapped_column(
        ForeignKey("country.id", ondelete="RESTRICT", onupdate="CASCADE")
    )

    # Scraping status
    scraped_boulders: Mapped[Optional[bool]] = mapped_column(
        Boolean, default=False
    )
    boulders_scraped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    boulder_scrape_error: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )
    boulder_retry_count: Mapped[int] = mapped_column(Integer, default=0)
    scraping_resume_grade_correspondence: Mapped[Optional[int]] = (
        mapped_column(Integer, nullable=True)
    )
    scraping_resume_page: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Relationship
    country: Mapped["models.country.Country"] = relationship(
        "Country", back_populates="areas"
    )
    crags: Mapped[Optional[List["models.crag.Crag"]]] = relationship(
        back_populates="area"
    )

    def __repr__(self):
        return f"<Area(name: {self.name}, slug: {self.slug}, country_id: {self.country_id})>"

    @classmethod
    def get_by_slug(cls, db_session, slug: str):
        """Retrieve an Area by its slug."""
        return db_session.scalar(select(cls).where(cls.slug == slug))

    def update_scraping_resume_page(self, db_session, page_index: int):
        """Update the scraping resume checkpoint page for the Area."""
        self.scraping_resume_page = page_index
        db_session.add(self)
        db_session.commit()
        db_session.refresh(self)
        return self

    def update_scraping_resume_grade(self, db_session, grade_correspondence: int):
        """Update the scraping resume checkpoint grade for the Area."""
        self.scraping_resume_grade_correspondence = grade_correspondence
        db_session.add(self)
        db_session.commit()
        db_session.refresh(self)
        return self
    
    def mark_as_scraped(self, db_session):
        """Mark the Area as having all boulders scraped."""
        self.scraped_boulders = True
        self.scraping_resume_page = None
        self.scraping_resume_grade_correspondence = None
        self.boulders_scraped_at = datetime.now()
        db_session.add(self)
        db_session.commit()
        db_session.refresh(self)
        return self