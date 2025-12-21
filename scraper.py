from time import time

from database import Session, drop_tables, initialize_empty_db
from scraping.boulder import boulder_scraping    



if __name__ == "__main__":
    drop_tables()
    initialize_empty_db()
    start = time()
    with Session() as db:
        
        boulder_scraping(db)
    end = time()

    print(f"Execution time: {end - start:.4f} seconds")