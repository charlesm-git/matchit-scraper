from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from models.area import Area
from models.boulder import Boulder
from models.crag import Crag
from models.grade import Grade


db_path = "matchit.db"

DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, echo=False)

session = Session(bind=engine)

area = 'ticino'

boulders_with_ascents = session.scalars(
    select(func.count(Boulder.id))
    .join(Boulder.crag)
    .join(Crag.area)
    .where(Boulder.ascents.any(), Area.slug == area)
).all()

boulders = session.scalars(
    select(func.count(Boulder.id))
    .join(Boulder.crag)
    .join(Crag.area)
    .where(Area.slug == area)
).all()

print(f'Boulders with ascents: {boulders_with_ascents[0]} / {boulders[0]}')
