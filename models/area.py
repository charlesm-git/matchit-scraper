from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Integer, select

from models.base import Base
import models.region
import models.boulder


class Area(Base):
    __tablename__ = "area"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String)
    name_normalized: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    region_id: Mapped[int] = mapped_column(
        ForeignKey("region.id", ondelete="RESTRICT", onupdate="CASCADE")
    )

    # Relationship
    region: Mapped["models.region.Region"] = relationship(
        "Region", back_populates="areas"
    )
    boulders: Mapped[Optional[List["models.boulder.Boulder"]]] = relationship(
        back_populates="area"
    )

    def __repr__(self):
        return f"<Area(name: {self.name}, url: {self.url}, status: {self.status})>"

    @classmethod
    def get_all(cls, db):
        areas = db.scalars(select(cls)).all()
        return areas
