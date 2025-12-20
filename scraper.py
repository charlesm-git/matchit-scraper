import asyncio
from time import time

import aiohttp
from database import Session, drop_tables, initialize_empty_db
from scraping.area_scraping import scrape_regions, scrape_all_areas


async def main():
    drop_tables()
    initialize_empty_db()
    start = time()
    with Session() as db:
        async with aiohttp.ClientSession() as session:
            await scrape_regions(session=session, db=db)
            await scrape_all_areas(session=session, db=db)
    end = time()

    print(f"Execution time: {end - start:.4f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
