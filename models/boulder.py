from typing import Optional, List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Float, Integer, String, ForeignKey

from models.base import Base
from models.boulder_style import boulder_style_table
from models.boulder_setter import boulder_setter_table
import models.grade
import models.area
import models.style
import models.user
import models.ascent


class Boulder(Base):
    __tablename__ = "boulder"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String)
    name_normalized: Mapped[str] = mapped_column(String)
    grade_id: Mapped[int] = mapped_column(ForeignKey("grade.id"))
    slash_grade_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("grade.id"), nullable=True, default=None
    )
    area_id: Mapped[int] = mapped_column(ForeignKey("area.id"))
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    number_of_rating: Mapped[int] = mapped_column(Integer, default=0)
    url: Mapped[str] = mapped_column(String, unique=True)

    # Relationship to other entities via Foreign Keys
    grade: Mapped["models.grade.Grade"] = relationship(
        "Grade", back_populates="boulders", foreign_keys=[grade_id]
    )
    slash_grade: Mapped[Optional["models.grade.Grade"]] = relationship(
        "Grade", foreign_keys=[slash_grade_id]
    )
    area: Mapped["models.area.Area"] = relationship(
        "Area", back_populates="boulders"
    )

    # Many-to-Many relationship to styles and setters using core tables
    styles: Mapped[List["models.style.Style"]] = relationship(
        secondary=boulder_style_table, back_populates="boulders"
    )
    setters: Mapped[List["models.user.User"]] = relationship(
        secondary=boulder_setter_table, back_populates="set_boulders"
    )

    # Association object for ascents
    ascents: Mapped[List["models.ascent.Ascent"]] = relationship(
        "Ascent", back_populates="boulder"
    )

    def __repr__(self):
        return f"<Boulder(name: {self.name}, grade: {self.grade.value}, setters: {self.setters}, Ascents: {self.ascents})"
