import os
from scholar.api import crawl
from scholar.post_maker import make_all
from scholar.database import create_tables

SEARCH_TERM = '"simulation-based+inference"'


def reset() -> None:
    """Rebuild the database from scratch and remake all md files."""

    if os.path.exists("scholar/paper.db"):
        os.remove("scholar/paper.db")

    create_tables()
    crawl(SEARCH_TERM)
    make_all(overwrite=True)


if __name__ == "__main__":
    # crawl(SEARCH_TERM)  # For crawling all results (start a new database)
    crawl(
        SEARCH_TERM, stop_days=14
    )  # For crawling only the last 14 days (simulate google scholar alerts)

    make_all(overwrite=False)
