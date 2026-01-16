from datetime import datetime
from multiprocessing import synchronize
import random
import signal
import sys
from time import sleep
from typing import List
from sqlalchemy.orm import scoped_session
from sqlalchemy import delete, select
import requests

from database import Session
from models.area import Area
from models.ascent import Ascent
from models.boulder import Boulder
from models.country import Country
from models.crag import Crag
from models.grade import Grade
from scraping.fetch import fetch
from scraping.helper import signal_handler, text_normalizer
from scraping import helper


def scrape_area(
    country_normalized_name: str,
    area_config: dict,
    force_rescrape: bool,
    boulders_count: int,
    ascents_count: int,
):
    """Scrape all boulders for a given area by scraping each crag"""
    signal.signal(signal.SIGINT, signal_handler)

    with Session() as db:
        # Ensure country and area exist
        country: Country = Country.get_by_normalized_name(
            db, country_normalized_name
        )
        area: Area = Area.get_by_slug(db, area_config["area_slug"])

        # Create country and area if they do not exist
        if not country:
            country = Country.create(
                db,
                name=country_normalized_name.title(),
                name_normalized=country_normalized_name,
                slug=country_normalized_name.replace(" ", "-"),
            )
        if not area:
            # Construct area URL
            if area_config["is_crag_in_db"]:
                url = f"https://www.8a.nu/crags/bouldering/{country.slug}/{area_config["area_external_slug"]}"
            else:
                url = f"https://www.8a.nu/areas/{country.slug}/{area_config["area_external_slug"]}/"

            area = Area.create(
                db,
                name=area_config["area_name"],
                name_normalized=text_normalizer(area_config["area_name"]),
                slug=area_config["area_slug"],
                external_slug=area_config.get("area_external_slug"),
                country_id=country.id,
                url=url,
                boulders_count=boulders_count,
                ascents_count=ascents_count,
            )
        elif area and boulders_count != "" and ascents_count != "":
            # Update boulders and ascents count if area already exists
            # and new counts are provided
            area.boulders_count = boulders_count
            area.ascents_count = ascents_count
            db.add(area)
            db.commit()

        # Check if area has already been fully scraped
        # If so, and force_rescrape is not set, skip scraping
        # If force_rescrape is set, delete existing boulders and ascents first, then rescrape
        if area.scraped_at is not None:
            if force_rescrape:
                print(
                    f"\nForce rescrape enabled. Deleting all boulders and ascents "
                    f"in area '{area.name}' of country '{country.name}'."
                )
                print("Press Ctrl+C twice within 10 seconds to cancel...")
                sleep(10)  # Pause to allow user to cancel if needed

                # Delete all boulders and ascents in the area
                reinitialize_area(db, area, full_reset=True)
                print("Deletion complete. Starting rescrape...\n")
            else:
                print(
                    f"\nArea '{area.name}' in country '{country.name}' has already been fully scraped."
                )
                update = input(
                    "Do you want to update this area? Boulders will be updated with new infos (y/n): "
                )
                if update.lower() != "y":
                    print(
                        "\nUse --delete-and-rescrape-entire-area to scrape the area completely again.\n"
                        "This will delete all boulders and ascents and rescrape from scratch.\n"
                    )
                    return
                else:
                    reinitialize_area(db, area, full_reset=False)
                    print("Area reinitialized. Starting update...\n")

        # Determine scraping path based on area configuration
        is_crag_in_db = area_config.get("is_crag_in_db", False)
        single_layer_division = area_config.get("single_layer_division", False)

        if not is_crag_in_db and not single_layer_division:
            # Path 1: Normal architecture - discover crags from API, scrape crag-by-crag
            scrape_path_area_double_layer(db, country, area, area_config)

        elif is_crag_in_db and single_layer_division:
            # Path 2: Crag as area, single layer - area duplicated as synthetic crag
            scrape_path_crag_as_area_single_layer(db, country, area)

        elif is_crag_in_db and not single_layer_division:
            # Path 3: Crag as area, double layer - area-level scraping with dynamic sector discovery
            scrape_path_crag_as_area_double_layer(db, country, area)

        else:  # not is_crag_in_db and single_layer_division
            # Path 4: Area, single layer - area-level scraping linked to synthetic crag
            scrape_path_area_single_layer(db, country, area)

        # Mark area as fully scraped
        area.mark_as_scraped(db)

        # Cleanup stale data (crags and boulders no longer in API)
        cleanup_stale_data(db, area)

    print("\n" + "=" * 80)
    print("Area scraped successfully. All crags and boulders fetched.")
    print("=" * 80 + "\n")


def scrape_path_area_double_layer(
    db: scoped_session,
    country: Country,
    area: Area,
    area_config: dict,
):
    """Path 1: Normal architecture - discover crags from API, scrape crag-by-crag"""
    # Discover all crags to scrape
    if area.scraped_crags_at is not None:
        crags_to_scrape = Crag.get_all_by_area_id(db, area.id)
    else:
        crags_from_main_area = discover_crags_from_api(db, country.slug, area)
        orphaned_crags = get_orphaned_crags(
            db, country.slug, area, area_config
        )
        crags_to_scrape = crags_from_main_area + orphaned_crags

        area.scraped_crags_at = datetime.now()
        db.add(area)
        db.commit()

    print(f"\n{len(crags_to_scrape)} crags to scrape:")

    # Scrape each crag
    for i, crag in enumerate(crags_to_scrape):
        print(f"\n{'='*80}")
        print(f"Scraping crag {i+1}/{len(crags_to_scrape)}: {crag.name}")
        print(f"{'='*80}\n")

        if crag.scraped_boulders_at is not None:
            print(f"Crag '{crag.name}' already scraped. Skipping.\n")
            continue

        scrape_crag_path_area_double_layer(
            db=db,
            country=country,
            area=area,
            crag=crag,
        )

        if helper.shutdown_requested:
            print(
                "\nShutdown complete. Progress saved. Resume by running again."
            )
            sys.exit(0)


def scrape_crag_path_area_double_layer(
    db: scoped_session,
    country: Country,
    area: Area,
    crag: Crag,
):
    """Scrape a single crag"""
    # Determine starting page/grade for resume
    page_index = (
        crag.scraping_resume_page
        if crag.scraping_resume_page is not None
        else 0
    )

    # Scrape all boulders for this crag

    # crag API url templates (use {page_index} placeholder for dynamic updates)
    base_url = (
        f"https://www.8a.nu/api/unification/outdoor/v1/web/zlaggables/bouldering/{country.slug}"
        f"?sectorSlug&pageIndex={{page_index}}&sortField=name"
        f"&grade=16,36&searchQuery&order=asc&cragSlug={crag.slug}"
    )
    referer = (
        f"https://www.8a.nu/crags/bouldering/{country.slug}/{crag.slug}/routes"
        f"?grade=16,36&sortField=name&order=asc&page={{page_index}}"
    )

    # Handle different scraping modes
    scrape_boulders_by_location(
        db=db,
        country=country,
        area=area,
        crag=crag,
        page_index=page_index,
        api_url=base_url,
        referer=referer,
    )

    # Reset page index after first grade
    page_index = 0

    # Mark crag as fully scraped
    crag.mark_as_scraped(db)
    print(f"Crag '{crag.name}' fully scraped.\n")


def scrape_path_area_single_layer(
    db: scoped_session,
    country: Country,
    area: Area,
):
    """Path 2: Area, single layer - area-level scraping linked to synthetic crag"""
    # Create or get synthetic crag for the area
    crag = Crag.get_by_slug_and_area_id(
        db, slug=area.external_slug, area_id=area.id
    )
    if not crag:
        crag = Crag.create(
            db,
            name=area.name,
            name_normalized=area.name_normalized,
            slug=area.external_slug,
            area_id=area.id,
            url=area.url,
            is_synthetic=True,
        )
        area.scraped_crags_at = datetime.now()
        db.add(area)
        db.commit()

    print(f"\nScraping area '{area.name}' as single layer (synthetic crag)\n")

    if crag.scraped_boulders_at is None:
        scrape_crag_path_area_single_layer(db, country, area, crag)
    else:
        print(f"Crag '{crag.name}' already scraped.\n")


def scrape_crag_path_area_single_layer(
    db: scoped_session,
    country: Country,
    area: Area,
    crag: Crag,
):
    """Scrape using crag-as-area API (area API endpoint)"""
    # Determine starting page/grade for resume
    page_index = (
        crag.scraping_resume_page
        if crag.scraping_resume_page is not None
        else 0
    )

    # Scrape all grades for this crag

    # Area API url templates (use {page_index} placeholder for dynamic updates)
    base_url = (
        f"https://www.8a.nu/api/unification/outdoor/v1/web/zlaggables/1/{country.slug}"
        f"?pageIndex={{page_index}}&grade=16,36&sortField=name"
        f"&order=asc&areaSlug={area.external_slug}"
    )
    referer = (
        f"https://www.8a.nu/areas/{country.slug}/{area.external_slug}/bouldering"
        f"?grade=16,36&sortField=name&order=asc&page={{page_index}}"
    )

    # Handle different scraping modes
    scrape_boulders_by_location(
        db=db,
        country=country,
        area=area,
        crag=crag,
        page_index=page_index,
        api_url=base_url,
        referer=referer,
    )

    # Mark crag as fully scraped
    crag.mark_as_scraped(db)
    print(f"Crag '{crag.name}' fully scraped.\n")


def scrape_path_crag_as_area_double_layer(
    db: scoped_session,
    country: Country,
    area: Area,
):
    """Path 3: Crag as area, double layer - area-level scraping with dynamic sector discovery"""
    print(f"\nScraping area '{area.name}' with dynamic sector discovery\n")

    scrape_crags_path_crag_as_area_double_layer(db, country, area)


def scrape_crags_path_crag_as_area_double_layer(
    db: scoped_session,
    country: Country,
    area: Area,
):
    """Scrape crag-level-API with dynamic sector discovery as crags"""
    # Determine starting page/grade for resume
    page_index = (
        area.scraping_resume_page
        if area.scraping_resume_page is not None
        else 0
    )

    # Scrape all boulders for this crag

    # crag API url templates (use {page_index} placeholder for dynamic updates)
    base_url = (
        f"https://www.8a.nu/api/unification/outdoor/v1/web/zlaggables/bouldering/{country.slug}"
        f"?sectorSlug&pageIndex={{page_index}}&sortField=name"
        f"&grade=16,36&searchQuery&order=asc&cragSlug={area.external_slug}"
    )
    referer = (
        f"https://www.8a.nu/crags/bouldering/{country.slug}/{area.external_slug}/routes"
        f"?grade=16,36&sortField=name&order=asc&page={{page_index}}"
    )

    # Handle different scraping modes
    scrape_boulders_by_location(
        db=db,
        country=country,
        area=area,
        page_index=page_index,
        api_url=base_url,
        referer=referer,
    )

    # Mark all crags in area as fully scraped
    all_crags = Crag.get_all_by_area_id(db, area.id)
    for crag in all_crags:
        crag.mark_as_scraped(db)
        print(f"Crag '{crag.name}' fully scraped.\n")

    # Mark crag as fully scraped
    area.mark_as_scraped(db)
    print(f"Area '{area.name}' fully scraped.\n")


def scrape_path_crag_as_area_single_layer(
    db: scoped_session,
    country: Country,
    area: Area,
):
    """Path 4: Crag as area, single layer - area duplicated as synthetic crag"""
    # Create or get synthetic crag that duplicates the area
    crag = Crag.get_by_slug_and_area_id(
        db, slug=area.external_slug, area_id=area.id
    )
    if not crag:
        crag = Crag.create(
            db,
            name=area.name,
            name_normalized=area.name_normalized,
            slug=area.external_slug,
            area_id=area.id,
            url=area.url,
            is_synthetic=True,
        )
        area.scraped_crags_at = datetime.now()
        db.add(area)
        db.commit()

    print(f"\nScraping synthetic crag: {crag.name}\n")

    if crag.scraped_boulders_at is None:
        scrape_crags_path_crag_as_area_single_layer(db, country, area, crag)
    else:
        print(f"Crag '{crag.name}' already scraped.\n")


def scrape_crags_path_crag_as_area_single_layer(
    db: scoped_session,
    country: Country,
    area: Area,
    crag: Crag,
):
    """Scrape crag-level-API with dynamic sector discovery as crags"""
    # Determine starting page/grade for resume
    page_index = (
        crag.scraping_resume_page
        if crag.scraping_resume_page is not None
        else 0
    )

    # Scrape all boulders for this crag
    # crag API url templates (use {page_index} placeholder for dynamic updates)
    base_url = (
        f"https://www.8a.nu/api/unification/outdoor/v1/web/zlaggables/bouldering/{country.slug}"
        f"?sectorSlug&pageIndex={{page_index}}&sortField=name"
        f"&grade=16,36&searchQuery&order=asc&cragSlug={area.external_slug}"
    )
    referer = (
        f"https://www.8a.nu/crags/bouldering/{country.slug}/{area.external_slug}/routes"
        f"?grade=16,36&sortField=name&order=asc&page={{page_index}}"
    )

    # Handle different scraping modes
    scrape_boulders_by_location(
        db=db,
        country=country,
        area=area,
        crag=crag,
        page_index=page_index,
        api_url=base_url,
        referer=referer,
    )

    # Mark all crags in area as fully scraped
    all_crags = Crag.get_all_by_area_id(db, area.id)
    for crag in all_crags:
        crag.mark_as_scraped(db)
        print(f"Crag '{crag.name}' fully scraped.\n")

    # Mark crag as fully scraped
    area.mark_as_scraped(db)
    print(f"Area '{area.name}' fully scraped.\n")


def discover_crags_from_api(
    db: scoped_session,
    country_slug: str,
    area: Area,
) -> list[Crag]:
    """Discover crags for an area from the 8a.nu API"""
    crags = []
    page_index = 0

    while True:
        base_url = (
            f"https://www.8a.nu/api/unification/outdoor/v1/web/crags?"
            f"pageIndex={page_index}&sortField=totalascents&category=69"
            f"&order=desc&countrySlug={country_slug}&areaSlug={area.external_slug}"
        )
        referer = f"https://www.8a.nu/areas/{country_slug}/{area.external_slug}/crags?page={page_index + 1}"
        response = fetch(url=base_url, referer=referer)
        items = response.get("items", [])
        pagination = response.get("pagination", {})

        for item in items:
            if item.get("category") != 1:  # Skip non-bouldering crags
                continue

            crag = Crag.get_by_slug_and_area_id(
                db, slug=item.get("cragSlug"), area_id=area.id
            )
            if not crag:
                crag = Crag.create(
                    db,
                    name=item.get("cragName"),
                    name_normalized=text_normalizer(item.get("cragName")),
                    slug=item.get("cragSlug"),
                    area_id=area.id,
                    url=f"https://www.8a.nu/crags/bouldering/{country_slug}/{item.get('cragSlug')}/routes",
                )
            crag.scraped_at = datetime.now()
            db.add(crag)
            crags.append(crag)

        if not pagination.get("hasNext"):
            break
        page_index += 1

    return crags


def get_orphaned_crags(
    db: scoped_session,
    country_slug: str,
    area: Area,
    area_config: dict,
) -> list[Crag]:
    """Add any manually configured orphaned crags to the area"""
    crags = []
    for added_crag_config in area_config.get("added_crags", []):
        crag_obj = Crag.get_by_slug_and_area_id(
            db, slug=added_crag_config["slug"], area_id=area.id
        )
        if not crag_obj:
            crag_obj = Crag.create(
                db,
                name=added_crag_config["name"],
                name_normalized=text_normalizer(added_crag_config["name"]),
                slug=added_crag_config["external_slug"],
                area_id=area.id,
                url=f"https://www.8a.nu/crags/bouldering/{country_slug}/{added_crag_config['external_slug']}/routes",
            )
        crag_obj.scraped_at = datetime.now()
        db.add(crag_obj)
        crags.append(crag_obj)
    return crags


def reinitialize_area(
    db: scoped_session, area: Area, full_reset: bool = False
):
    """Delete all boulders and ascents in the given area (all crags)"""
    if full_reset:
        delete_all_ascents_in_area(db, area)
        delete_all_boulders_in_area(db, area)
        delete_all_crags_in_area(db, area)
    else:
        update_boulders_and_crags_for_rescrape(db, area)

    # Reset area scraping status
    area.scraped_at = None
    area.scraped_crags_at = None
    area.scraping_resume_page = None
    db.add(area)

    db.commit()


def delete_all_boulders_in_area(db: scoped_session, area: Area):
    """Delete all boulders in the given area"""
    crag_ids = select(Crag.id).where(Crag.area_id == area.id)
    db.execute(delete(Boulder).where(Boulder.crag_id.in_(crag_ids)))
    db.commit()


def delete_all_ascents_in_area(db: scoped_session, area: Area):
    """Delete all ascents in the given area"""
    boulder_ids = (
        select(Boulder.id).join(Boulder.crag).where(Crag.area_id == area.id)
    )
    db.execute(delete(Ascent).where(Ascent.boulder_id.in_(boulder_ids)))
    db.commit()


def delete_all_crags_in_area(db: scoped_session, area: Area):
    """Delete all crags in the given area"""
    db.execute(delete(Crag).where(Crag.area_id == area.id))
    db.commit()


def update_boulders_and_crags_for_rescrape(db: scoped_session, area: Area):
    """Mark all boulders in the area as not scraped for update"""
    crags: List[Crag] = Crag.get_all_by_area_id(db, area.id)
    for crag in crags:
        crag.scraped_at = None
        crag.scraped_boulders_at = None
        crag.scraping_resume_page = None
        db.add(crag)
    db.commit()

    boulders: List[Boulder] = (
        db.execute(
            select(Boulder).join(Boulder.crag).where(Crag.area_id == area.id)
        )
        .scalars()
        .all()
    )
    for boulder in boulders:
        boulder.scraped_at = None
        boulder.scraped_ascents_at = None
        db.add(boulder)
    db.commit()


def cleanup_stale_data(db: scoped_session, area: Area):
    """Delete boulders and crags that were not found during the most recent scrape"""
    # Delete stale boulders (not seen during this scrape)
    boulder_ids = (
        select(Boulder.id)
        .join(Boulder.crag)
        .where(Crag.area_id == area.id)
        .where(Boulder.scraped_at.is_(None))
    )
    result = db.execute(delete(Boulder).where(Boulder.id.in_(boulder_ids)))
    deleted_boulders = result.rowcount

    # Delete stale crags (not seen during this scrape)
    result = db.execute(
        delete(Crag)
        .where(Crag.area_id == area.id)
        .where(Crag.scraped_at.is_(None))
    )
    deleted_crags = result.rowcount

    db.commit()

    if deleted_boulders > 0 or deleted_crags > 0:
        print(
            f"\nCleaned up stale data: {deleted_boulders} boulders, {deleted_crags} crags"
        )


def scrape_boulders_by_location(
    db: scoped_session,
    country: Country,
    area: Area,
    api_url: str,
    referer: str,
    page_index: int,
    crag: Crag = None,
):
    """Fetch boulder's data from a boulder page"""
    retry_count = 0
    max_retries = 3

    while True:
        print(f"Current page - {page_index}")
        # Random sleep to avoid rate limiting
        sleep(random.uniform(1, 5))

        # Format URLs with current page_index
        current_api_url = api_url.format(page_index=page_index)
        current_referer = referer.format(page_index=page_index + 1)

        try:
            response = fetch(url=current_api_url, referer=current_referer)
            retry_count = 0
        except requests.exceptions.Timeout as e:
            print(f"Timeout fetching page {page_index}: {e}")
            retry_count += 1
            if retry_count >= max_retries:
                error_msg = (
                    f"Timeout after {max_retries} retries on page {page_index}"
                )
                print(f"ERROR: {error_msg}")
                if crag:
                    crag.boulder_scrape_error = error_msg
                    db.add(crag)
                    db.commit()
                else:
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
            print(f"HTTP {status_code} error on page {page_index}: {e}")
            retry_count += 1
            if retry_count >= max_retries:
                error_msg = f"HTTP {status_code} after {max_retries} retries on page {page_index}"
                print(f"ERROR: {error_msg}")
                if crag:
                    crag.boulder_scrape_error = error_msg
                    db.add(crag)
                    db.commit()
                else:
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
            print(f"Request error on page {page_index}: {e}")
            retry_count += 1
            if retry_count >= max_retries:
                error_msg = f"Request failed after {max_retries} retries on page {page_index}"
                print(f"ERROR: {error_msg}")
                if crag:
                    crag.boulder_scrape_error = error_msg
                    db.add(crag)
                    db.commit()
                else:
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

        extract_boulders_info(
            db=db,
            items=items,
            area=area,
            country=country,
            crag=crag,
        )

        if pagination.get("hasNext"):
            page_index += 1
            print(
                f"\n{pagination.get('pageCount') - page_index} pages remaining."
            )
            if crag:
                crag.update_scraping_resume_page(db, page_index)
            else:
                area.update_scraping_resume_page(db, page_index)

            # Check for graceful shutdown
            if helper.shutdown_requested:
                print(
                    "\nShutdown complete. Progress saved. Resume by running again."
                )
                sys.exit(0)
        else:
            if crag:
                crag.update_scraping_resume_page(db, 0)
            else:
                area.update_scraping_resume_page(db, 0)

            # Check for graceful shutdown
            if helper.shutdown_requested:
                print(
                    "\nShutdown complete. Progress saved. Resume by running again."
                )
                sys.exit(0)
            break


def extract_boulders_info(
    db: scoped_session,
    items: list[dict],
    area: Area,
    country: Country,
    crag: Crag = None,
) -> list[dict]:
    """Extract relevant boulder information from API response items"""
    for item in items:
        grade_value = item.get("difficulty")
        grade = Grade.get_by_value(db, grade_value)

        boulder_name = item.get("zlaggableName")

        # Skip boulders with name "N.N." or similar
        # Also skip boulders with zero ascents
        if boulder_name.lower() == "n.n." or item.get("totalAscents", 0) == 0:
            continue

        boulder = Boulder.get_by_slug(db, item.get("zlaggableSlug"))

        if not boulder:
            boulder = Boulder()

        boulder.external_db_id = item.get("zlaggableId")

        boulder.name = boulder_name
        boulder.name_normalized = text_normalizer(boulder_name)

        boulder.slug = item.get("zlaggableSlug")

        boulder.category = item.get("category")
        boulder.rating = item.get("averageRating")

        boulder.sector_name = item.get("sectorName")
        boulder.sector_slug = item.get("sectorSlug")

        boulder.crag_slug = item.get("cragSlug")
        boulder.crag_name = item.get("cragName")

        boulder.grade_id = grade.id

        boulder.scraped_at = datetime.now()
        boulder.scraped_ascents_at = None

        # Associate boulder with crag
        # If crag is provided, use it directly
        # Otherwise, discover or create crag based on sector
        if crag:
            boulder.crag_id = crag.id
        else:
            # Dynamic crag discovery based on sector
            sector_slug = item.get("sectorSlug")
            crag_obj = Crag.get_by_slug_and_area_id(
                db, slug=sector_slug, area_id=area.id
            )
            if not crag_obj:
                crag_obj = Crag.create(
                    db,
                    name=item.get("sectorName"),
                    name_normalized=text_normalizer(item.get("sectorName")),
                    slug=sector_slug,
                    area_id=area.id,
                    url=(
                        f"https://www.8a.nu/crags/bouldering/{country.slug}/"
                        f"{area.slug}/sectors/{sector_slug}/routes"
                    ),
                )
            crag_obj.scraped_at = datetime.now()
            db.add(crag_obj)
            boulder.crag_id = crag_obj.id

        boulder.url = (
            f"https://www.8a.nu/crags/bouldering/{country.slug}/{item.get('cragSlug')}"
            f"/sectors/{item.get('sectorSlug')}/routes/{boulder.slug}"
        )

        db.add(boulder)
    db.commit()
