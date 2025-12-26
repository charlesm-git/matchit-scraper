from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, select

from models.base import Base
import models.area


class Country(Base):
    __tablename__ = "country"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String)
    name_normalized: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String)

    # Relationship
    areas: Mapped[Optional[List["models.area.Area"]]] = relationship(
        back_populates="country"
    )

    def __repr__(self):
        return f"<Country(name: {self.name}, slug: {self.slug})>"

    @classmethod
    def get_by_slug(cls, db_session, slug: str):
        """Retrieve a Country by its slug."""
        return db_session.scalar(select(cls).where(cls.slug == slug))
    
    @classmethod
    def get_by_normalized_name(cls, db_session, name_normalized: str):
        """Retrieve a Country by its normalized name."""
        return db_session.scalar(
            select(cls).where(cls.name_normalized == name_normalized)
        )
