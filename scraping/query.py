from sqlalchemy import select

from models.area import Area
from models.boulder import Boulder
from models.crag import Crag


def fetch_all_boulders_in_area(db, area_slug):
    """Fetch all boulders in a given area."""
    return (
        db.scalars(
            select(Boulder)
            .join(Boulder.crag)
            .join(Crag.area)
            .where(Area.slug == area_slug)
        )
        .all()
    )

def fetch_unscraped_boulders_in_area(db, area_slug):
    """Fetch boulders in a given area that have not had their ascents scraped yet."""
    return (
        db.scalars(
            select(Boulder)
            .join(Boulder.crag)
            .join(Crag.area)
            .where(
                Area.slug == area_slug,
                Boulder.scraped_ascents == False,
            )
            .order_by(Boulder.last_ascent_scrape_attempt.asc().nullsfirst())
        )
        .all()
    )