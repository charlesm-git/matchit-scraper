# Bleau.info Scraper

This scraper is designed for **personal use only** to scrape data from the [bleau.info](https://bleau.info/) website. It collects information on regions, areas, boulders, public repetitors, and ascents. The scraper uses asynchronous Python with `aiohttp` for efficient scraping of more than 40,000 pages and stores the data in a SQLite database managed by SQLAlchemy.

## Features

- **Asynchronous Scraping:** Efficiently scrapes the site using Python's `asyncio` and `aiohttp`.
- **SQLite Database:** Stores the scraped data in a SQLite database, managed via SQLAlchemy.
- **Data Stored:**
  - Areas (name, region, boulders, etc.)
  - Boulders (name, grade, style, etc.)
  - Public Users and Ascents

## Database Models

The SQLite database is organized with the following models:

- **Boulder**
- **Area**
- **Region**
- **Grade**
- **User**
- **Style**
- **Ascent** (association table between Boulder and User)
- **Boulder_Style** (association table between Boulder and Style)
- **Boulder_Setter** (association table between Boulder and User)

## License

This project is for **personal use only**. All rights reserved to the original website owner. Ensure compliance with the site's `robots.txt` or terms of service regarding scraping.

## Notes

- Scraping a large website like bleau.info may take some time. You can monitor the progress through logging.
- Make sure to respect the site's `robots.txt` or terms of service regarding scraping.