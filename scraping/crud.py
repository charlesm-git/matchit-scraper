from sqlalchemy import select

from database import Session
from models.area import Area
from models.boulder import Boulder
from models.country import Country
from models.crag import Crag


def fetch_all_boulders(db):
    """Fetch all boulders in the database."""
    return db.scalars(select(Boulder)).all()


def fetch_unscraped_boulders(db):
    """Fetch boulders that have not had their ascents scraped yet."""
    return db.scalars(
        select(Boulder)
        .where(Boulder.scraped_ascents_at.is_(None))
        .order_by(Boulder.last_ascent_scrape_attempt.asc().nullsfirst())
    ).all()


def fetch_all_boulders_in_area(db, area_slug):
    """Fetch all boulders in a given area."""
    return db.scalars(
        select(Boulder)
        .join(Boulder.crag)
        .join(Crag.area)
        .where(Area.slug == area_slug)
    ).all()


def fetch_unscraped_boulders_in_area(db, area_slug):
    """Fetch boulders in a given area that have not had their ascents scraped yet."""
    return db.scalars(
        select(Boulder)
        .join(Boulder.crag)
        .join(Crag.area)
        .where(
            Area.slug == area_slug,
            Boulder.scraped_ascents_at.is_(None),
        )
        .order_by(Boulder.last_ascent_scrape_attempt.asc().nullsfirst())
    ).all()


def update_area_counts(
    country: str, area_config: dict, boulders_count: int, ascents_count: int
):
    """Update area counts for boulders and ascents."""
    with Session() as session:
        area_obj = session.scalar(
            select(Area)
            .join(Area.country)
            .where(
                Area.slug == area_config["area_slug"],
                Country.name_normalized == country,
            ),
        )

        if not area_obj:
            print(
                f"Error: Area '{area_config['area']}' not found in country '{country}'"
            )
            return

        area_obj.boulders_count = boulders_count
        area_obj.ascents_count = ascents_count
        session.add(area_obj)
        session.commit()

        print("Area counts updated successfully.")
