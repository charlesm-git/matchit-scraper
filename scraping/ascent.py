from datetime import datetime
import random
import signal
import sys
from time import sleep
import requests
from sqlalchemy import select
from sqlalchemy.orm import scoped_session

from config import AUTHENTICATION_COOKIE
from database import Session
from models.area import Area
from models.ascent import Ascent
from models.boulder import Boulder
from models.crag import Crag
from models.grade import Grade
from models.sector import Sector
from models.user import User
from scraping.fetch import fetch
from scraping.helper import text_normalizer
from scraping import helper


def scrape_ascents_for_boulders_in_area(area_slug: str):
    """Scrape ascents for all boulders in the specified area."""
    signal.signal(signal.SIGINT, helper.signal_handler)

    with Session() as db:
        boulders = db.scalars(
            select(Boulder)
            .join(Boulder.sector)
            .join(Sector.crag)
            .join(Crag.area)
            .where(
                Area.slug == area_slug,
                Boulder.scraped_ascents == False,
            )
            .order_by(Boulder.last_ascent_scrape_attempt.asc().nullsfirst())
        ).all()

        for boulder in boulders:
            scrape_ascents_from_boulder(db, boulder)


def scrape_ascents_from_boulder(db: scoped_session, boulder: Boulder):
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

        # Build API URL
        api_url = (
            f"https://www.8a.nu/api/unification/ascent/v1/web/crags/bouldering"
            f"/{boulder.sector.crag.area.country.slug}/{boulder.sector.crag.slug}"
            f"/sectors/{boulder.sector.slug}/routes/{boulder.slug}"
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
            if item.get("userPrivate"):
                continue

            # Get or create user
            user = User.get_by_slug(db, item.get("userSlug"))
            if not user:
                user: User = User.create(
                    db,
                    name=item.get("userName"),
                    name_normalized=text_normalizer(item.get("userName")),
                    slug=item.get("userSlug"),
                )

            grade = Grade.get_by_correspondence(db, item.get("zlagGradeIndex"))
            if not grade and item.get("zlagGradeIndex") is not None:
                print(
                    f"Unknown grade correspondence for index {item.get('zlagGradeIndex')}"
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
            ascent.is_FA = item.get("firstAscent")
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
                    "\nShutdown requested. Ascents for current boulder will have to be re-scraped."
                )
                sys.exit(0)
        else:
            if helper.shutdown_requested:
                print(
                    "\nShutdown requested. Ascents for current boulder will have to be re-scraped."
                )
            break

    # Bulk save ascents to the database
    db.add_all(ascents)
    db.commit()
    # Mark boulder as scraped
    boulder.mark_as_scraped(db)

    print(f"Scraped {len(ascents)} ascents for boulder {boulder.name}")
