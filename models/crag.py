from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, ForeignKey, String, Integer, select

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
        ForeignKey("area.id", ondelete="RESTRICT", onupdate="CASCADE")
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
