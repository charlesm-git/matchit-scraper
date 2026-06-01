# Match-It Scraper

Scraper and similarity engine for the Match-It bouldering platform. Collects boulder and ascent data from [8a.nu](https://www.8a.nu/) across multiple countries and computes boulder-to-boulder similarity matrices used by the recommendation system.

**For personal use only.**

## Tech Stack

- **Scraping:** Requests (synchronous)
- **Database:** PostgreSQL (Neon) via SQLAlchemy
- **ML/Similarity:** SciPy, NumPy, Pandas, scikit-learn
- **Fuzzy Matching:** RapidFuzz (for deduplication)
- **Package Manager:** Poetry

## Features

### Scraping
- Scrape boulders, crags, areas, users, and ascents from 8a.nu
- Resume capability — scraping can be stopped and restarted with progress tracking
- Handles complex area structures (added crags, single-layer divisions, synthetic crags)
- Configurable per-area scraping options

### Similarity Engine
- **Ascent-based similarity:** Jaccard similarity on user-boulder co-ascent matrices
- **Grade-based similarity:** Grade proximity weighting between boulders
- **Combined scoring:** Weighted combination of ascent and grade similarity
- Matrix cleaning, CSR conversion, and storage in the database

### Scripts
- `script/scraper.py` — Main scraper (boulders, ascents, full reset)
- `script/similarity.py` — Compute and store similarity matrices
- `script/deduplicate.py` — Find and merge duplicate boulders
- `script/update_area_numbers.py` — Refresh area boulder/ascent counts
- `script/create_indexes.py` — Create database indexes
- `script/cleanup.py` — Database cleanup utilities
- `script/migration.py` — Schema migrations

## Supported Areas

| Country | Areas |
|---------|-------|
| Austria | Silvretta |
| France | Fontainebleau |
| Italy | Val Daone, Val di Mello, Varazze |
| Spain | Albarracín |
| Sweden | Västervik |
| Switzerland | Bas-Valais, Magic Wood, Ticino |

Areas are configured in `config.py` under `VALID_COUNTRY_AREAS`.

## Project Structure

```
matchit-scraper/
├── config.py              # Area configuration & constants
├── database.py            # SQLAlchemy engine & session
├── scraping/              # Scraping logic (fetch, parse, CRUD)
├── ml/                    # Similarity computation
│   ├── ascents_similarity.py
│   ├── grade_similarity.py
│   ├── matrix_cleaning.py
│   └── crud.py
├── models/                # SQLAlchemy models
├── script/                # Runnable scripts
└── ml/notebooks/          # Jupyter notebooks for exploration
```

## Database Models

- **Country** / **Area** / **Crag** — Geographic hierarchy
- **Boulder** — Name, grade, location
- **User** — Public climber profiles
- **Ascent** — Boulder × User association
- **Grade** — Grade scale with numeric correspondence
- **Similarity** — Precomputed boulder similarity scores

## Usage

```bash
# Install dependencies
poetry install

# Scrape boulders for an area
python script/scraper.py -c switzerland -a ticino -sb

# Scrape ascents for an area
python script/scraper.py -c switzerland -a ticino -sa

# Scrape ascents for all boulders in the database
python script/scraper.py -sa

# Compute similarity matrices
python script/similarity.py -c switzerland -a ticino

# Reset database (destructive — requires confirmation)
python script/scraper.py --reset
```

## License

For **personal use only**. All data rights belong to the original website owner. Ensure compliance with the site's terms of service.
