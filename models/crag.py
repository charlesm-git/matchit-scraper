from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Integer, select

from models.base import Base
import models.area
import models.sector


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

    # Foreign Key
    area_id: Mapped[int] = mapped_column(
        ForeignKey("area.id", ondelete="RESTRICT", onupdate="CASCADE")
    )

    # Relationship
    area: Mapped["models.area.Area"] = relationship(
        "Area", back_populates="crags"
    )
    sectors: Mapped[Optional[List["models.sector.Sector"]]] = relationship(
        back_populates="crag"
    )

    def __repr__(self):
        return f"<Crag(name: {self.name}, slug: {self.slug}, area_id: {self.area_id})>"

    @classmethod
    def get_by_slug(cls, db_session, slug: str):
        """Retrieve a Crag by its slug."""
        return db_session.scalar(select(cls).where(cls.slug == slug))
