# Bleau.info Scraper

This scraper is designed for **personal use only** to scrape data from the [bleau.info](https://bleau.info/) website. It collects information on regions, areas, boulders, public repetitors, and ascents. The scraper uses asynchronous Python with `aiohttp` for efficient scraping of more than 40,000 pages and stores the data in a SQLite database managed by SQLAlchemy.

## Features

- **Asynchronous Scraping:** Efficiently scrapes the site using Python's `asyncio` and `aiohttp`.
- **SQLite Database:** Stores the scraped data in a SQLite database, managed via SQLAlchemy.
- **Resume Capability:** Scraping can be stopped and resumed at any point with progress tracking
- **Added Crags Support:** Handle orphaned crags that should belong to a parent area but have their own pagination
- **Data Stored:**
  - Areas (name, region, boulders, etc.)
  - Boulders (name, grade, style, etc.)
  - Public Users and Ascents

## Configuration

Areas and crags are configured in [config.py](config.py) under `VALID_COUNTRY_AREAS`. Each area can have:

- `scrape_as_crag`: Whether to scrape as a crag with pagination
- `use_synthetic_crag`: Whether to create a synthetic crag wrapper
- `added_crags`: List of crags that should be under this area but have their own pagination system

### Added Crags

Some locations have crags that are improperly split on 8a.nu - they should be part of a parent area but have their own pagination system. Use `added_crags` to scrape these:

```python
{
    "area": "ticino",
    "area_slug": "ticino",
    "area_name": "Ticino",
    "scrape_as_crag": False,
    "use_synthetic_crag": False,
    "added_crags": [
        {"name": "Bodio", "slug": "bodio"},
        {"name": "Osogna", "slug": "osogna"},
    ],
}
```


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
