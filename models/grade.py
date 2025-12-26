from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship, scoped_session
from sqlalchemy import Integer, SmallInteger, String, select

from models.base import Base
import models.boulder


class Grade(Base):
    __tablename__ = "grade"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    value: Mapped[str] = mapped_column(String(3))
    correspondence: Mapped[int] = mapped_column(SmallInteger)
    eightanu_correspondence: Mapped[int] = mapped_column(SmallInteger)

    # Relationship
    boulders: Mapped[List["models.boulder.Boulder"]] = relationship(
        back_populates="grade"
    )
    ascents: Mapped[List["models.ascent.Ascent"]] = relationship(
        "Ascent", back_populates="log_grade"
    )

    def __repr__(self):
        return f"<Grade: {self.value}, {self.correspondence}>"

    @classmethod
    def get_by_correspondence(cls, db, correspondence_value):
        return db.scalar(
            select(cls).where(cls.correspondence == correspondence_value)
        )
        
    @classmethod
    def get_by_eightanu_correspondence(cls, db, eightanu_correspondence_value):
        return db.scalar(
            select(cls).where(
                cls.eightanu_correspondence == eightanu_correspondence_value
            )
        )

    @classmethod
    def get_by_value(cls, db, value):
        return db.scalar(select(cls).where(cls.value == value))

    @classmethod
    def get_by_min_max_value(
        cls, db: scoped_session, min_value: str = None, max_value: str = None
    ):
        min_value = min_value if min_value is not None else "1"
        max_value = max_value if max_value is not None else "9A+"

        min_corr = db.scalar(
            select(cls.correspondence).where(cls.value == min_value)
        )
        max_corr = db.scalar(
            select(cls.correspondence).where(cls.value == max_value)
        )
        return db.scalars(
            select(cls).where(
                cls.correspondence >= min_corr, cls.correspondence <= max_corr
            )
        ).all()
