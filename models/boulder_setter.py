from sqlalchemy import Table, Column, ForeignKey

from models.base import Base

boulder_setter_table = Table(
    "boulder_setter",
    Base.metadata,
    Column("boulder_id", ForeignKey("boulder.id"), primary_key=True),
    Column("user_id", ForeignKey("user.id"), primary_key=True),
)
