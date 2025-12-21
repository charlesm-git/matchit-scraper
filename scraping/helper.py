import string
import unicodedata
from urllib.parse import urljoin
from models.user import User
# from scraping.fetch import BASE_URL


# def user_existance_check(user, db):
#     """Check the existance of a user in the database from a username.
#     If it doesn't exist, adds it.
#     return: a User instance"""
#     user_url = urljoin(BASE_URL, user["url"])

#     user_object = db.query(User).where(User.url == user_url).first()
#     if user_object:
#         return user_object

#     user_object = User(
#         username=user["username"],
#         username_normalized=text_normalizer(user["username"]),
#         url=user_url,
#     )
#     db.add(user_object)
#     db.flush()
#     return user_object


def text_normalizer(text: str):
    # Decompose accents
    text = unicodedata.normalize("NFD", text)
    # Remove decomposed part of accents to only keep letter
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    # Lower case aggressively
    text = text.casefold()

    return text
