import os
from pathlib import Path
from scholar.api import query_arxiv, query_serp, query_biorxiv
from scholar.post_maker import make_all
from scholar.database import create_tables, insert_result

SEARCH_TERM = '"simulation-based+inference"'
POST_DIR = Path("./_posts/")


def crawl(term: str, more_results: bool = False, stop_days: int = None) -> dict:
    """Crawl the SERP API for snippets containing the given term.

    Args:
        term (str): The term to search for.
        more_results (bool): If true search in everything instead of abstract.
        stop_days (int): Stop crawling when the oldest result is older than this.
    """
    next_url = None
    while True:

        # Initial query from SERP API to get new papers
        results = query_serp(url=next_url, term=term, more_results=more_results)


        for result in results["formatted_results"]:
            
            # Append extra arxiv data
            if result['journal'] == 'arxiv.org':
                arxiv_data = query_arxiv(result["title"])
                if arxiv_data is not None:
                    result.update(arxiv_data)

            # Append extra biorxiv data
            if result['journal'] == 'biorxiv.org':
                biorxiv_data = query_biorxiv(result["doi"])
                if biorxiv_data is not None:
                    result.update(biorxiv_data)

            # Insert into database
            insert_result(result)
            max_days_since_added = result["days_since_added"]

        # Only use the search term on the first SERP API query, use next_url for the rest
        term = None  

        # Exit if we have reached the stopping condition or there are no more results
        if stop_days is not None and max_days_since_added > stop_days:
            break
        try:
            next_url = results["serpapi_pagination"]["next"]
        except KeyError:
            break


if __name__ == "__main__":
    crawl(SEARCH_TERM, stop_days=90)

    # The single source of truth is in the database, so we delete all to avoid publish date offset by one bug due to timezone.
    for post in POST_DIR.glob("*.md"):
        post.unlink()

    make_all()


def reset() -> None:
    """Rebuild the database from scratch and remake all md files."""

    if os.path.exists("scholar/paper.db"):
        os.remove("scholar/paper.db")

    create_tables()
    crawl(SEARCH_TERM)
    make_all(overwrite=True)
