from datetime import date
from sqlalchemy import Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
import models.boulder


class Similarity(Base):
    __tablename__ = "similarity"

    id1: Mapped[int] = mapped_column(
        Integer, ForeignKey("boulder.id"), primary_key=True
    )
    id2: Mapped[int] = mapped_column(
        Integer, ForeignKey("boulder.id"), primary_key=True
    )
    score: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[date] = mapped_column(Date, default=date.today)

    # Relationships
    boulder1: Mapped["models.boulder.Boulder"] = relationship(
        "Boulder", foreign_keys=[id1]
    )
    boulder2: Mapped["models.boulder.Boulder"] = relationship(
        "Boulder", foreign_keys=[id2]
    )
