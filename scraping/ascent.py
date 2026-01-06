from datetime import datetime
import random
import signal
import sys
from time import sleep
import requests
from sqlalchemy.orm import scoped_session

from config import AUTHENTICATION_COOKIE
from database import Session
from models.ascent import Ascent
from models.boulder import Boulder
from models.grade import Grade
from models.user import User
from scraping import helper
from scraping.fetch import fetch
from scraping.crud import (
    fetch_all_boulders,
    fetch_all_boulders_in_area,
    fetch_unscraped_boulders,
    fetch_unscraped_boulders_in_area,
)


def scrape_ascents_for_boulders(
    area_config: dict = None, force_rescrape: bool = False
):
    """Scrape ascents for all boulders in the specified area."""
    signal.signal(signal.SIGINT, helper.signal_handler)

    with Session() as db:
        # Handle force rescrape option
        if force_rescrape:
            print(
                f"Force rescrape enabled. Deleting current database content for "
                f"{area_config['area_name'] if area_config else 'entire database'} and rescraping."
            )
            print("\nPress Ctrl+C twice within 10 seconds to cancel.\n")
            sleep(10)

            # Fetch all boulders (in area if specified)
            if area_config is None:
                boulders = fetch_all_boulders(db)
            else:
                boulders = fetch_all_boulders_in_area(
                    db, area_config["area_slug"]
                )

            # Delete all ascents for these boulders
            for boulder in boulders:
                db.query(Ascent).filter(
                    Ascent.boulder_id == boulder.id
                ).delete(synchronize_session=False)
                # Mark boulder as not scraped
                boulder.scraped_ascents = False
                db.add(boulder)
            db.commit()
            print(
                f"Deleted all ascents for boulders in {area_config['area_name'] if area_config else 'entire database'}."
            )

        print(
            f"\nStarting ascent scraping {area_config['area_name'] if area_config else 'entire database'}"
        )

        # Fetch boulders that need ascents scraped
        if area_config is None:
            unscraped_boulders = fetch_unscraped_boulders(db)
        else:
            unscraped_boulders = fetch_unscraped_boulders_in_area(
                db, area_config["area_slug"]
            )

        print(
            f"Found {len(unscraped_boulders)} boulders to scrape ascents for.\n"
        )

        # If no boulders to scrape, exit
        if not unscraped_boulders:
            print(
                f"All boulders in {area_config['area_name'] if area_config else 'entire database'} have already been scraped."
            )
            print(
                f"Use --delete-and-rescrape-all-ascents to force rescraping."
            )
            print("Exiting.")
            return

        # Scrape ascents for each boulder
        for boulder in unscraped_boulders:
            scrape_ascents_from_boulder(db, boulder)


def scrape_ascents_from_boulder(
    db: scoped_session, boulder: Boulder
):
    """Scrape ascents for a given boulder URL and store them in the database."""
    retry_count = 0
    max_retries = 3
    page_index = 0

    ascents = []

    # Update last ascent scrape attempt time
    boulder.update_last_ascent_scrape_attempt(db)

    while True:
        print(
            f"Scraping ascents for boulder {boulder.name} (page {page_index})"
        )

        # Random sleep to avoid rate limiting
        sleep(random.uniform(1, 5))

        api_url = (
            f"https://www.8a.nu/api/unification/ascent/v1/web/crags/bouldering"
            f"/{boulder.crag.area.country.slug}/{boulder.crag_slug}"
            f"/sectors/{boulder.sector_slug}/routes/{boulder.slug}"
            f"/ascents?pageIndex={page_index}&sortField=date&order=desc"
        )

        # Set referer to boulder page
        referer = boulder.url
        if page_index > 0:
            referer += f"?page={page_index + 1}"

        # Fetch ascents data from API
        try:
            response = fetch(
                url=api_url,
                random_headers=False,
                referer=referer,
                authentication_cookie=AUTHENTICATION_COOKIE,
            )
            retry_count = 0
        except requests.exceptions.Timeout as e:
            print(
                f"Timeout fetching page {page_index} for boulder {boulder.name}: {e}"
            )
            retry_count += 1
            if retry_count >= max_retries:
                error_msg = (
                    f"Timeout after {max_retries} retries on page {page_index}"
                )
                print(f"ERROR: {error_msg}")
                boulder.ascent_scrape_error = error_msg
                db.add(boulder)
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
                f"HTTP {status_code} error on page {page_index} for boulder {boulder.name}: {e}"
            )
            retry_count += 1
            if retry_count >= max_retries:
                error_msg = f"HTTP {status_code} after {max_retries} retries on page {page_index}"
                print(f"ERROR: {error_msg}")
                boulder.ascent_scrape_error = error_msg
                db.add(boulder)
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
                f"Request error on page {page_index} for boulder {boulder.name}: {e}"
            )
            retry_count += 1
            if retry_count >= max_retries:
                error_msg = f"Request failed after {max_retries} retries on page {page_index}"
                print(f"ERROR: {error_msg}")
                boulder.ascent_scrape_error = error_msg
                db.add(boulder)
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

        # Process ascents here (implement your ascent parsing logic)
        for item in items:

            # Skip private users
            if item.get("userPrivate") or item.get("userName") is None:
                continue

            # Get or create user
            user = User.get_by_slug(db, item.get("userSlug"))
            if not user:
                user: User = User.create(
                    db,
                    name=item.get("userName"),
                    name_normalized=helper.text_normalizer(
                        item.get("userName")
                    ),
                    slug=item.get("userSlug"),
                )

            grade = Grade.get_by_value(db, item.get("difficulty"))
            if not grade and item.get("difficulty") is not None:
                print(
                    f"Unknown grade correspondence for 'difficulty' {item.get('difficulty')}"
                )
                print(f"Skipping ascent by user {user.name}")

            ascent = Ascent()

            ascent.boulder_id = boulder.id
            ascent.user_id = user.id
            ascent.log_grade_id = grade.id if grade else None

            ascent.external_db_id = item.get("ascentId")
            ascent.source = 1
            ascent.rating = item.get("rating")
            ascent.log_date = datetime.fromisoformat(
                item.get("date")[:10]
            ).date()
            ascent.comment = item.get("comment")

            ascent_type = item.get("ascentType")
            match ascent_type:
                case "f":
                    ascent.type = "flash"
                case "os":
                    ascent.type = "onsight"
                case "rp":
                    ascent.type = "redpoint"
                case "go":
                    ascent.type = "go"
                case _:
                    ascent.type = None

            ascent.with_kneepad = item.get("withKneepad")
            ascent.is_fa = item.get("firstAscent")
            ascent.is_soft = item.get("isSoft")
            ascent.is_hard = item.get("isHard")
            ascent.is_repeat = item.get("repeat")
            ascent.is_overhang = item.get("isOverhang")
            ascent.is_vertical = item.get("isVertical")
            ascent.is_slab = item.get("isSlab")
            ascent.is_roof = item.get("isRoof")
            ascent.is_athletic = item.get("isAthletic")
            ascent.is_endurance = item.get("isEndurance")
            ascent.is_crimpy = item.get("isCrimpy")
            ascent.is_cruxy = item.get("isCruxy")
            ascent.is_sloper = item.get("isSloper")
            ascent.is_technical = item.get("isTechnical")
            ascent.project = item.get("project")
            ascent.recommended = item.get("recommended")

            ascents.append(ascent)

        if pagination.get("hasNext"):
            page_index += 1

            if helper.shutdown_requested:
                print(
                    "\nShutting down. Ascents for current boulder will have to be re-scraped."
                )
                sys.exit(0)
        else:
            if helper.shutdown_requested:
                print(
                    "\nShutting down. Ascents for current boulder will have to be re-scraped."
                )
                sys.exit(0)
            break

    # Bulk save ascents to the database
    db.add_all(ascents)
    db.commit()
    # Mark boulder as scraped
    boulder.mark_as_scraped(db)

    print(f"Scraped {len(ascents)} ascents for boulder {boulder.name}\n")
