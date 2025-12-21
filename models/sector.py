from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Integer, select

from models.base import Base
import models.crag
import models.boulder


class Sector(Base):
    __tablename__ = "sector"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    name_normalized: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String)
    external_db_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Foreign Key
    crag_id: Mapped[int] = mapped_column(
        ForeignKey("crag.id", ondelete="RESTRICT", onupdate="CASCADE")
    )

    # Relationship
    crag: Mapped["models.crag.Crag"] = relationship("Crag", back_populates="sectors")
    boulders: Mapped[Optional[List["models.boulder.Boulder"]]] = relationship(
        back_populates="sector"
    )

    def __repr__(self):
        return f"<Sector(name: {self.name}, slug: {self.slug}, crag_id: {self.crag_id})>"
