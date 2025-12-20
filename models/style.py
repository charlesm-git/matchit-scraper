from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String

from models.base import Base
from models.boulder_style import boulder_style_table
import models.boulder


class Style(Base):
    __tablename__ = "style"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    style: Mapped[str] = mapped_column(String)

    # Relationship
    boulders: Mapped[List["models.boulder.Boulder"]] = relationship(
        secondary=boulder_style_table, back_populates="styles"
    )
