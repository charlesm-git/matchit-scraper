from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Integer, select

from models.base import Base
import models.area
import models.boulder


class Crag(Base):
    __tablename__ = "crag"

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
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)

    # Foreign Key
    area_id: Mapped[int] = mapped_column(
        ForeignKey("area.id", ondelete="RESTRICT", onupdate="CASCADE"),
        index=True,
    )

    # Scraping status (for crags with their own pagination)
    scraped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=datetime.now()
    )
    scraped_boulders_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    boulder_scrape_error: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )
    boulder_retry_count: Mapped[int] = mapped_column(Integer, default=0)
    scraping_resume_page: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Relationship
    area: Mapped["models.area.Area"] = relationship(
        "Area", back_populates="crags"
    )
    boulders: Mapped[Optional[List["models.boulder.Boulder"]]] = relationship(
        back_populates="crag"
    )

    def __repr__(self):
        return f"<Crag(name: {self.name}, slug: {self.slug}, area_id: {self.area_id})>"

    @classmethod
    def get_by_slug_and_area_id(cls, db_session, slug: str, area_id: int):
        """Retrieve a Crag by its slug and area_id."""
        return db_session.scalar(
            select(cls).where(cls.slug == slug, cls.area_id == area_id)
        )

    @classmethod
    def get_all_by_area_id(cls, db_session, area_id: int):
        """Retrieve all Crags by their area_id."""
        return db_session.scalars(
            select(cls).where(cls.area_id == area_id)
        ).all()

    def update_scraping_resume_page(self, db_session, page_index: int):
        """Update the scraping resume checkpoint page for the Crag."""
        self.scraping_resume_page = page_index
        db_session.add(self)
        db_session.commit()
        db_session.refresh(self)
        return self

    def update_scraping_resume_grade(
        self, db_session, grade_correspondence: int
    ):
        """Update the scraping resume checkpoint grade for the Crag."""
        self.scraping_resume_grade_correspondence = grade_correspondence
        db_session.add(self)
        db_session.commit()
        db_session.refresh(self)
        return self

    def mark_as_scraped(self, db_session):
        """Mark the Crag as having all boulders scraped."""
        self.scraping_resume_page = None
        self.scraping_resume_grade_correspondence = None
        self.scraped_boulders_at = datetime.now()
        db_session.add(self)
        db_session.commit()
        db_session.refresh(self)
        return self
