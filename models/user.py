from typing import List, Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, select

from models.base import Base
import models.ascent


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String)
    name_normalized: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationship
    ascents: Mapped[List["models.ascent.Ascent"]] = relationship(
        "Ascent", back_populates="user"
    )

    def __repr__(self):
        return f"<User(id: {self.id}, username: {self.name})>"

    @classmethod
    def get_by_slug(cls, db, slug_value: str):
        return db.scalar(
            select(cls).where(cls.slug == slug_value)
        )