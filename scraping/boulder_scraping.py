import re
from datetime import date
from urllib.parse import urljoin

from sqlalchemy.exc import IntegrityError

from scraping.helper import (
    styles_existance_check,
    text_normalizer,
    user_existance_check,
)
from scraping.fetch import fetch, BASE_URL
from models.boulder import Boulder
from models.ascent import Ascent
from models.grade import Grade


async def boulder_scraping(session, db, boulder_relative_url, area_id):
    """Fetch boulder's data from a boulder page"""
    url = urljoin(BASE_URL, boulder_relative_url)

    soup = await fetch(session, boulder_relative_url)

    title = soup.find("h3")
    # Extract the name and the grade from the header
    name = list(title.children)[0].strip()
    name_normalized = text_normalizer(name)

    grade = list(title.find("em").children)[0].get_text().strip()
    grade_id = Grade.get_id_from_value(db=db, grade_value=grade)

    # Extract slash grade
    slash_grade_id = None
    slash_grade = title.find("span", class_="ag")
    if slash_grade:
        slash_grade = slash_grade.get_text().strip()
        slash_grade_id = Grade.get_id_from_value(
            db=db, grade_value=slash_grade
        )

    # Extract styles
    styles = None
    scraped_styles = soup.find("div", class_="btype").get_text().strip()
    if scraped_styles != "-":
        styles = scraped_styles

    # Extract setters
    setters = None
    scraped_setters = (
        soup.find("div", class_="row bhead")
        .find("div", class_="col-md-12")
        .find("div")
        .find_all("a")
    )
    if scraped_setters is not None:
        setters = [
            {"username": setter.get_text().strip(), "url": setter.get("href")}
            for setter in scraped_setters
        ]

    # Initialise the rating and the number of ascents to default values
    rating = None
    number_of_rating = 0

    # If any, extract the rating and the number of rating
    first_bopins = soup.find("div", class_="bdetails").find(
        "div", class_="bopins"
    )
    if first_bopins:
        title = first_bopins.find("strong").get_text()
        if title in ["Appréciation", "Average rating"]:
            # Rating extraction
            rating = first_bopins.find_all("li")[2]
            rating = rating.get_text().strip().split(" ")[0].replace(",", ".")
            # Number of rating extraction
            number_of_rating = first_bopins.find_all("li")[3]
            number_of_rating = number_of_rating.get_text().strip()
            match = re.match(r"\((\d+).*", number_of_rating)
            number_of_rating = int(match.group(1))

    # Create the boulder instance based on non nullable parameters
    boulder = Boulder.create(
        db=db,
        name=name,
        name_normalized=name_normalized,
        grade_id=grade_id,
        slash_grade_id=slash_grade_id,
        area_id=area_id,
        url=url,
        rating=rating,
        number_of_rating=number_of_rating,
    )

    # Update the styles in the database
    if styles:
        styles = styles.split(",")
        styles = [style.strip() for style in styles]
        # Convert styles names into style objects
        for style in styles:
            try:
                with db.begin_nested():
                    style = styles_existance_check(style=style, db=db)
                    boulder.styles.append(style)
            except IntegrityError:
                print(
                    f"Style '{style}' duplicated for boulder {boulder.name} - skipped"
                )

    # Update the setters in the database
    if setters:
        # Convert username into User object
        for setter in setters:
            try:
                with db.begin_nested():
                    setter = user_existance_check(user=setter, db=db)
                    boulder.setters.append(setter)
            except IntegrityError:
                print(
                    f"Setter '{setter}' duplicated for boulder {boulder.name} - skipped"
                )

    # Scrape and save in the database all the ascents logged
    ascents = soup.find_all("div", class_="repetition")

    for ascent in ascents:
        children = list(ascent.children)

        # Extract the date of the ascent
        log_date = children[0]
        day, month, year = log_date.split("-")
        year = year.strip().replace(":", "")
        log_date = date(int(year), int(month), int(day))

        # Extract the name of the repetitor
        repetitor = {
            "username": children[1].get_text().strip(),
            "url": children[1].get("href"),
        }
        repetitor = user_existance_check(user=repetitor, db=db)

        try:
            with db.begin_nested():
                ascent = Ascent(
                    boulder_id=boulder.id,
                    user_id=repetitor.id,
                    log_date=log_date,
                )
                db.add(ascent)
        except IntegrityError:
            print(
                f"Skipped ascent by {repetitor.username} on {log_date} for boulder {boulder.name}"
            )
    db.commit()
