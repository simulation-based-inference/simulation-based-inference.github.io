from typing import Optional
import os
import requests
from dotenv import load_dotenv
from .database import insert_serp_results

load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")


def query_serp(
    url: str = None, term: str = None, more_results: bool = False
) -> Optional[dict]:
    """Query the SERP API for snippets containing the given term.

    Args:
        url (str): API URL. If None, use the default.
        term (str): The term to search for.
        more_results (bool): If true search in everything instead of abstract.
    """
    params = {"api_key": SERP_API_KEY}
    scisbd = 2 if more_results else 1

    if url is None:
        url = "https://serpapi.com/search"
        params.update(
            {
                "engine": "google_scholar",
                "q": term,
                "hl": "en",
                "num": 20,  # Maxed out at 20
                "scisbd": scisbd,
                "as_vis": 1,
            }
        )

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(
            f"Request failed with status code {response.status_code}: {response.text}"
        )


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
        term = None  # Only use the term on the first page, next_url already has it

        days_since_added = insert_serp_results(results)
        if stop_days is not None and days_since_added > stop_days:
            break
        try:
            next_url = results["serpapi_pagination"]["next"]
        except KeyError:
            break


############################## Obsolete ##############################
def query_xdd(term: str) -> Optional[dict]:
    """Query the XDD API for snippets containing the given term."""
    url = "https://xdd.wisc.edu/api/snippets"
    params = {"term": term, "article_limit": 1000}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(
            f"Request failed with status code {response.status_code}: {response.text}"
        )
