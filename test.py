from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models.boulder import Boulder


db_path = "bleau_info_stats.db"

DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, echo=False)

session = Session(bind=engine)

boulders = session.scalars(select(Boulder).limit(10)).all()

for boulder in boulders:
    print(boulder)
