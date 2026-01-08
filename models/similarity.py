from datetime import date
from sqlalchemy import Date, Float, ForeignKey, Index, Integer, desc
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
    score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[date] = mapped_column(Date, default=date.today)

    __table_args__ = (
        Index('ix_similarity_id1_score_desc', 'id1', desc('score')),
    )

    # Relationships
    boulder1: Mapped["models.boulder.Boulder"] = relationship(
        "Boulder", foreign_keys=[id1]
    )
    boulder2: Mapped["models.boulder.Boulder"] = relationship(
        "Boulder", foreign_keys=[id2]
    )
