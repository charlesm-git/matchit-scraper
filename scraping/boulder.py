import random
import signal
import sys
from time import sleep
from sqlalchemy.orm import scoped_session
import requests

from database import Session
from models import grade
from models.area import Area
from models.boulder import Boulder
from models.country import Country
from models.crag import Crag
from models.grade import Grade
from models.sector import Sector
from scraping.fetch import fetch
from scraping.helper import text_normalizer

# Graceful shutdown flag
shutdown_requested = False


def signal_handler(signum, frame):
    global shutdown_requested
    if shutdown_requested:
        print("\nForce quit.")
        sys.exit(1)
    shutdown_requested = True
    print("\nShutdown requested. Finishing current page...")


def scrape_area(country_arg: str, area_arg: str):
    """Scrape all boulders for a given area in a country"""
    signal.signal(signal.SIGINT, signal_handler)

    with Session() as db:
        # Ensure country and area exist
        country: Country = Country.get_by_slug(db, country_arg)
        area: Area = Area.get_by_slug(db, area_arg)
        # Get all grades
        grades: list[Grade] = Grade.get_by_min_max_value(db)

        # Create country and area if they do not exist
        if not country:
            country = Country.create(
                db,
                name=country_arg.capitalize(),
                name_normalized=country_arg,
                slug=country_arg,
            )
        if not area:
            area = Area.create(
                db,
                name=area_arg.capitalize(),
                name_normalized=area_arg,
                slug=area_arg,
                country_id=country.id,
            )

        # Determine starting page index
        page_index = None
        if not area.scraped_boulders and area.scraping_resume_page is not None:
            page_index = area.scraping_resume_page

        # Scrape boulders by grade
        for i, grade in enumerate(grades):
            # Skip grades already scraped
            if (
                area.scraping_resume_grade_correspondence
                and grade.correspondence
                < area.scraping_resume_grade_correspondence
            ):
                continue

            # Get next grade correspondence for checkpointing
            next_grade_corr = (
                grades[i + 1].correspondence if i + 1 < len(grades) else None
            )
            scrape_boulders_by_grade(
                db, country, area, grade, page_index, next_grade_corr
            )

        # Mark area as fully scraped
        area.mark_as_scraped(db)


def scrape_boulders_by_grade(
    db: scoped_session,
    country: Country,
    area: Area,
    grade: Grade,
    page_index: int = None,
    next_grade_correspondence: int = None,
):
    """Fetch boulder's data from a boulder page"""
    page_index = 0 if page_index is None else page_index
    retry_count = 0
    max_retries = 3

    while True:
        print(
            f"Scraping boulders for grade {grade} in area {area.name} (page {page_index})"
        )
        # Random sleep to avoid rate limiting
        sleep(random.uniform(1, 5))

        # Build URL with grade directly in query string to avoid encoding issues
        base_url = (
            f"https://www.8a.nu/api/unification/outdoor/v1/web/zlaggables/1/{country.slug}"
            f"?pageIndex={page_index}&grade={grade.correspondence},{grade.correspondence}&sortField=totalascents"
            f"&order=desc&areaSlug={area.slug}"
        )

        referer = f"https://www.8a.nu/areas/{country.slug}/{area.slug}/bouldering?grade={grade.correspondence},{grade.correspondence}"
        if page_index > 0:
            referer += f"&page={page_index + 1}"

        try:
            response = fetch(url=base_url, referer=referer)
            retry_count = 0
        except requests.exceptions.Timeout as e:
            print(f"Timeout fetching page {page_index} for grade {grade}: {e}")
            retry_count += 1
            if retry_count >= max_retries:
                error_msg = f"Timeout after {max_retries} retries on page {page_index} for grade {grade.value}"
                print(f"ERROR: {error_msg}")
                area.boulder_scrape_error = error_msg
                db.add(area)
                db.commit()
                sys.exit(1)
            wait_time = 2**retry_count
            print(
                f"Retrying in {wait_time}s... (attempt {retry_count}/{max_retries})"
            )
            sleep(wait_time)
            continue
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            print(
                f"HTTP {status_code} error on page {page_index} for grade {grade.value}: {e}"
            )
            retry_count += 1
            if retry_count >= max_retries:
                error_msg = f"HTTP {status_code} after {max_retries} retries on page {page_index} for grade {grade.value}"
                print(f"ERROR: {error_msg}")
                area.boulder_scrape_error = error_msg
                db.add(area)
                db.commit()
                sys.exit(1)
            wait_time = 2**retry_count
            print(
                f"Retrying in {wait_time}s... (attempt {retry_count}/{max_retries})"
            )
            sleep(wait_time)
            continue
        except requests.exceptions.RequestException as e:
            print(
                f"Request error on page {page_index} for grade {grade.value}: {e}"
            )
            retry_count += 1
            if retry_count >= max_retries:
                error_msg = f"Request failed after {max_retries} retries on page {page_index} for grade {grade.value}"
                print(f"ERROR: {error_msg}")
                area.boulder_scrape_error = error_msg
                db.add(area)
                db.commit()
                sys.exit(1)
            wait_time = 2**retry_count
            print(
                f"Retrying in {wait_time}s... (attempt {retry_count}/{max_retries})"
            )
            sleep(wait_time)
            continue

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
            boulder.grade_id = grade.id

            boulder.url = (
                f"https://www.8a.nu/crags/bouldering/{country.slug}/{crag.slug}"
                f"/sectors/{sector.slug}/routes/{boulder.slug}"
            )

            db.add(boulder)
        db.commit()
        if pagination.get("hasNext"):
            page_index += 1
            area.update_scraping_resume_page(db, page_index)

            # Check for graceful shutdown
            if shutdown_requested:
                print(
                    "\nShutdown complete. Progress saved. Resume by running again."
                )
                sys.exit(0)
        else:
            area.update_scraping_resume_page(db, None)
            area.update_scraping_resume_grade(db, next_grade_correspondence)

            # Check for graceful shutdown
            if shutdown_requested:
                print(
                    "\nShutdown complete. Progress saved. Resume by running again."
                )
                sys.exit(0)
            break
