import sys
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database import Session


with Session() as session:
    session.execute(text("ANALYZE;"))
    session.execute(text("VACUUM;"))
    session.commit()