import os
from scholar.api import query_arxiv, query_serp
from scholar.post_maker import make_all
from scholar.database import create_tables, insert_result

SEARCH_TERM = '"simulation-based+inference"'


def crawl(term: str, more_results: bool = False, stop_days: int = None) -> dict:
    """Crawl the SERP API for snippets containing the given term.

    Args:
        term (str): The term to search for.
        more_results (bool): If true search in everything instead of abstract.
        stop_days (int): Stop crawling when the oldest result is older than this.
    """
    next_url = None
    while True:
        results = query_serp(url=next_url, term=term, more_results=more_results)

        for result in results["formatted_results"]:
            # Append arXiv category and group
            arxiv_data = query_arxiv(result["title"])
            if arxiv_data is not None:
                result.update(arxiv_data)

            # Insert into database
            insert_result(result)
            max_days_since_added = result["days_since_added"]

        term = None  # Only use the term on the first page, next_url already has it

        if stop_days is not None and max_days_since_added > stop_days:
            break
        try:
            next_url = results["serpapi_pagination"]["next"]
        except KeyError:
            break


if __name__ == "__main__":
    # crawl(SEARCH_TERM)  # For crawling all results (start a new database)
    crawl(
        SEARCH_TERM, stop_days=14
    )  # For crawling only the last 14 days (simulate google scholar alerts)

    make_all(overwrite=False)


def reset() -> None:
    """Rebuild the database from scratch and remake all md files."""

    if os.path.exists("scholar/paper.db"):
        os.remove("scholar/paper.db")

    create_tables()
    crawl(SEARCH_TERM)
    make_all(overwrite=True)
