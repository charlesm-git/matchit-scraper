from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Integer, select

from models.base import Base
import models.area


class Country(Base):
    __tablename__ = "country"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    name_normalized: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String)

    # Relationship
    areas: Mapped[Optional[List["models.area.Area"]]] = relationship(
        back_populates="country"
    )

    def __repr__(self):
        return f"<Country(name: {self.name}, slug: {self.slug})>"
