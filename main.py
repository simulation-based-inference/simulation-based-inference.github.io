import datetime
import argparse
import logging
from backend.api import query_arxiv, query_serp, query_biorxiv
from backend.post_maker import remake_all_posts
from backend.database import insert_paper, Paper, get_paper, update_paper, get_papers
from backend.guess_category import Guesser

logging.basicConfig(level=logging.DEBUG)


SEARCH_TERM = '"simulation-based+inference"'
CATEGORY_GUESSER = Guesser()


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

            # Append guessed category
            if paper.category is None:
                paper.category = CATEGORY_GUESSER.guess(
                    paper.id, paper.title, paper.publication_info_summary
                )
                update_paper(paper)

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


def update_manual_category_group() -> None:
    """Update the manual category group in the database."""

    papers = get_papers()
    CATEGORY_GUESSER.regenerate_categories(papers)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--crawl", action="store_true")
    args = parser.parse_args()

    if args.crawl:
        crawl(SEARCH_TERM, stop_days=90)

    update_manual_category_group()  # Make sure changes made to guess_category_group.json are reflected in the database
    remake_all_posts()
