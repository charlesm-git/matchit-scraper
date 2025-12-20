from sqlalchemy import Table, Column, ForeignKey

from models.base import Base

boulder_style_table = Table(
    "boulder_style",
    Base.metadata,
    Column("boulder_id", ForeignKey("boulder.id"), primary_key=True),
    Column("style_id", ForeignKey("style.id"), primary_key=True),
)
