import asyncio
import re
from urllib.parse import urljoin

from scraping.helper import text_normalizer
from models.area import Area
from models.region import Region
from scraping.fetch import BASE_URL, fetch
from scraping.boulder_scraping import boulder_scraping


async def scrape_regions(session, db):
    """
    Scrape the sector page to extract the Regions.

    For each region:
    - Create a Region object and save it to the database.
    - Call get_areas_from_region()
    """
    relative_area_list_url = "/areas_by_region"
    soup = await fetch(session, relative_area_list_url)

    # Get each region row
    regions_rows = soup.find_all("div", class_="area_by_regions")

    # For each region row, isolate each region
    for regions_row in regions_rows:
        regions_div = regions_row.find_all("div", class_="bi-col-3 col-top")
        # For each region, Create a region object and scrape all areas.
        for region_item in regions_div:
            region_name = region_item.find("strong").get_text()
            region_name_normalized = text_normalizer(region_name)
            region = Region.create(
                db=db, name=region_name, name_normalized=region_name_normalized
            )

            scrape_areas_from_region(
                db=db, region_item=region_item, region=region
            )


def scrape_areas_from_region(db, region_item, region: Region):
    """From a 'Region' Beautifulsoup object, extract all the areas associated"""
    # Find the first occurrence of an 'a' tag
    areas_div = region_item.find_all("div")
    for div in areas_div:
        # Find the first occurrence of an 'a' tag
        area = div.find("a")
        if not area:
            continue

        # Extract useful data
        area_url = urljoin(BASE_URL, area.get("href"))
        area_name = area.get_text().strip()
        status = None
        match = re.match(r"(.+)\s\((.*?)\)", area_name)
        if match:
            area_name = match.group(1)
            status = match.group(2)
        area_name_normalized = text_normalizer(area_name)

        # Create the Area object
        area = Area(
            name=area_name,
            name_normalized=area_name_normalized,
            region_id=region.id,
            url=area_url,
            status=status,
        )
        db.add(area)
    db.commit()


async def scrape_all_areas(session, db):
    """
    Get all the areas from the database and scrape their urls for boulders
    """
    areas = Area.get_all(db=db)

    for area in areas:
        await scrape_boulders_from_area(
            area_url=area.url,
            area_id=area.id,
            db=db,
            session=session,
        )
    # tasks = [
    #     area_scraping(
    #         area_url=area.url,
    #         area_id=area.id,
    #         db=db,
    #         session=session,
    #     )
    #     for area in areas
    # ]
    # await asyncio.gather(*tasks)


async def scrape_boulders_from_area(session, area_url, area_id, db):
    """
    From an area url, scrape all the boulders urls associated.
    From each boulder url, call boulder_scraping().
    """
    soup = await fetch(session, area_url)
    boulders = soup.find_all("div", class_="vsr")

    boulder_urls = [boulder.find("a").get("href") for boulder in boulders]

    tasks = [
        boulder_scraping(
            session=session,
            db=db,
            boulder_relative_url=boulder_url,
            area_id=area_id,
        )
        for boulder_url in boulder_urls
    ]
    await asyncio.gather(*tasks)
