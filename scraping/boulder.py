import random
from time import sleep
from sqlalchemy.orm import scoped_session

from models.area import Area
from models.boulder import Boulder
from models.country import Country
from models.crag import Crag
from models.grade import Grade
from models.sector import Sector
from scraping.fetch import fetch
from scraping.helper import text_normalizer


def scrape_boulders_by_grade(
    db: scoped_session,
    country: Country,
    area: Area,
    grade: int,
    page_index: int = None,
):
    """Fetch boulder's data from a boulder page"""
    page_index = 0 if page_index is None else page_index

    while True:
        print(f"Scraping boulders for grade {grade} in area {area.name} (page {page_index})")
        # Build URL with grade directly in query string to avoid encoding issues
        base_url = (
            f"https://www.8a.nu/api/unification/outdoor/v1/web/zlaggables/1/{country.slug}"
            f"?pageIndex={page_index}&grade={grade},{grade}&sortField=totalascents"
            f"&order=desc&areaSlug={area.slug}"
        )

        referer = f"https://www.8a.nu/areas/{country.slug}/{area.slug}/bouldering?grade={grade},{grade}"
        if page_index > 0:
            referer += f"&page={page_index + 1}"

        try:
            response = fetch(url=base_url, referer=referer)
        except Exception as e:
            pass

        items = response.get("items", [])
        pagination = response.get("pagination", {})

        for item in items:

            crag = Crag.get_by_slug(db, item.get("cragSlug"))
            if not crag:
                crag_slug = item.get("cragSlug")
                crag: Crag = Crag.create(
                    db,
                    name=item.get("cragName"),
                    name_normalized=text_normalizer(item.get("cragName")),
                    external_db_id=item.get("cragId"),
                    slug=crag_slug,
                    area_id=area.id,
                    url=f"https://www.8a.nu/crags/bouldering/{country.slug}/{crag_slug}/routes",
                )

            sector = Sector.get_by_slug(db, item.get("sectorSlug"))
            if not sector:
                sector_slug = item.get("sectorSlug")
                sector: Sector = Sector.create(
                    db,
                    name=item.get("sectorName"),
                    name_normalized=text_normalizer(item.get("sectorName")),
                    external_db_id=item.get("sectorId"),
                    slug=sector_slug,
                    crag_id=crag.id,
                    url=f"https://www.8a.nu/crags/bouldering/{country.slug}/{crag.slug}/routes?sector={sector_slug}",
                )

            boulder = Boulder()

            boulder.external_db_id = item.get("zlaggableId")

            boulder_name = item.get("zlaggableName")
            boulder.name = boulder_name
            boulder.name_normalized = text_normalizer(boulder_name)

            boulder.slug = item.get("zlaggableSlug")

            boulder.category = item.get("category")
            boulder.rating = item.get("averageRating")

            boulder.sector_id = sector.id
            boulder.grade_id = grade

            boulder.url = (
                f"https://www.8a.nu/crags/bouldering/{country.slug}/{crag.slug}"
                f"/sector/{sector.slug}/routes/{boulder.slug}"
            )

            db.add(boulder)
        db.commit()
        if pagination.get("hasNext"):
            page_index += 1
            area.update_current_scraping_page(db, page_index)
        else:
            area.update_current_scraping_page(db, None)
            break
        sleep(random.uniform(1, 5))