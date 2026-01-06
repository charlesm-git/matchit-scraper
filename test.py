from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from models.area import Area
from models.base import Base
from models.boulder import Boulder
from models.crag import Crag
from models.grade import Grade
from models.similarity import Similarity


db_path = "matchit.db"

DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, echo=False)

Base.metadata.create_all(engine)


session = Session(bind=engine)

# area = "ticino"

# boulders_with_ascents = session.scalar(
#     select(func.count(Boulder.id))
#     .join(Boulder.crag)
#     .join(Crag.area)
#     .where(Boulder.ascents.any())
#     )

# boulders = session.scalar(select(func.count(Boulder.id)))

# print(f"Boulders with ascents: {boulders_with_ascents} / {boulders}")

boulder_id = 10843

boulder = session.get(Boulder, boulder_id)
print("Selected boulder:")
print(boulder)

print("\nSimilar boulders:")
similarities = session.execute(
    select(Boulder, Similarity.score)
    .join(Similarity, Boulder.id == Similarity.id2)
    .where(Similarity.id1 == 10843)
    .order_by(Similarity.score.desc())
    .limit(20)
).all()
for boulder, score in similarities:
    print(boulder, score)