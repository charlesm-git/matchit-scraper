# scraper/config.py
from pathlib import Path

# Paths
SCRAPER_DIR = Path(__file__).parent
API_DIR = Path(__file__).parent.parent / "api"

# Files
DB_FILE = "bleau_info_stats.db"
ASCENT_MATRIX_FILE = "similarity_ascent.npz"
GRADE_MATRIX_FILE = "similarity_grade.npz"
STYLE_MATRIX_FILE = "similarity_style.npz"


# Git
GIT_BRANCH = "main"
REMOTE_NAME = "origin"

VALID_COUNTRY_AREAS = {
    "switzerland": ["ticino"],
    "france": ["fontainebleau"],
}

AUTHENTICATION_COOKIE = "a8ca6c30-b0f4-40d9-b509-a7566eb36a4d"
