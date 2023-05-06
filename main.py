import datetime
import logging
from pathlib import Path
from scholar.api import query_arxiv, query_serp, query_biorxiv
from scholar.post_maker import remake_all_posts
from scholar.database import insert_paper, Paper, get_paper, update_paper

logging.basicConfig(level=logging.DEBUG)

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
        # Initial query from SERP API to get new papers
        results = query_serp(url=next_url, term=term, more_results=more_results)

        for result in results["formatted_results"]:
            # Append extra arxiv data
            if result["journal"] == "arxiv.org":
                arxiv_data = query_arxiv(result["arxiv_id"])
                if arxiv_data is not None:
                    result.update(arxiv_data)

            # Append extra biorxiv data
            if result["journal"] == "biorxiv.org":
                biorxiv_data = query_biorxiv(result["doi"])
                if biorxiv_data is not None:
                    result.update(biorxiv_data)

            # MUST Sanitize using Paper class, otherwise cannot get the correct title
            paper = Paper(**result)
            paper_from_db = get_paper(title=paper.title)

            if paper_from_db:
                paper.id = paper_from_db.id
                update_paper(paper)
            else:
                insert_paper(paper)

            # Update delta
            delta = datetime.datetime.now() - result["published_on"].replace(
                tzinfo=None
            )

        # Only use the search term on the first SERP API query, use next_url for the rest
        term = None

        # Exit if we have reached the stopping condition or there are no more results
        if stop_days is not None and delta.days > stop_days:
            break
        try:
            next_url = results["serpapi_pagination"]["next"]
        except KeyError:
            break


if __name__ == "__main__":
    crawl(SEARCH_TERM, stop_days=90)
    remake_all_posts()
