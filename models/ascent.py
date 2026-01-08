from datetime import date
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String

from models.base import Base
import models.boulder
import models.user
import models.grade


class Ascent(Base):
    __tablename__ = "ascent"

    # General attributes
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    external_db_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    source: Mapped[int] = mapped_column(Integer)
    log_date: Mapped[date] = mapped_column(Date)
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    type: Mapped[Optional[str]] = mapped_column(
        Enum("flash", "onsight", "redpoint", name="ascent_type"),
        nullable=True,
    )
    rating: Mapped[int] = mapped_column(Integer, default=0)

    # Boolean attributes
    with_kneepad: Mapped[bool] = mapped_column(Boolean, default=False)
    is_fa: Mapped[bool] = mapped_column(Boolean, default=False)
    is_soft: Mapped[bool] = mapped_column(Boolean, default=False)
    is_hard: Mapped[bool] = mapped_column(Boolean, default=False)
    is_repeat: Mapped[bool] = mapped_column(Boolean, default=False)
    is_overhang: Mapped[bool] = mapped_column(Boolean, default=False)
    is_vertical: Mapped[bool] = mapped_column(Boolean, default=False)
    is_slab: Mapped[bool] = mapped_column(Boolean, default=False)
    is_roof: Mapped[bool] = mapped_column(Boolean, default=False)
    is_athletic: Mapped[bool] = mapped_column(Boolean, default=False)
    is_endurance: Mapped[bool] = mapped_column(Boolean, default=False)
    is_crimpy: Mapped[bool] = mapped_column(Boolean, default=False)
    is_cruxy: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sloper: Mapped[bool] = mapped_column(Boolean, default=False)
    is_technical: Mapped[bool] = mapped_column(Boolean, default=False)
    project: Mapped[bool] = mapped_column(Boolean, default=False)
    recommended: Mapped[bool] = mapped_column(Boolean, default=False)

    # Foreign Keys
    boulder_id: Mapped[int] = mapped_column(ForeignKey("boulder.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    log_grade_id: Mapped[int] = mapped_column(ForeignKey("grade.id"))

    # Relationship
    boulder: Mapped["models.boulder.Boulder"] = relationship(
        "Boulder", back_populates="ascents"
    )
    user: Mapped["models.user.User"] = relationship(
        "User", back_populates="ascents"
    )
    log_grade: Mapped["models.grade.Grade"] = relationship(
        "Grade", back_populates="ascents"
    )

    def __repr__(self):
        return f"<Ascent({self.user}, {self.boulder}, date: {self.log_date}, type: {self.type})>"
