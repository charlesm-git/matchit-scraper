from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models.boulder import Boulder
from models.grade import Grade


db_path = "matchit.db"

DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, echo=False)

session = Session(bind=engine)

grades = Grade.get_by_min_max_value(session, min_value="6A")

for grade in grades:
    print(grade)