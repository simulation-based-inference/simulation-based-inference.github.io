import os
from dotenv import load_dotenv
import requests

load_dotenv()
SERP_API_KEY = os.getenv('SERP_API_KEY')

def query_serp(url: str = None, term: str = None, more_results: bool = False) -> dict | None:
    """Query the SERP API for snippets containing the given term.
    
    Args:
        url (str): API URL. If None, use the default.
        term (str): The term to search for.
        more_results (bool): If true search in everything instead of abstract.
    """

    params = {"api_key": SERP_API_KEY}
    scisbd = 2 if more_results else 1

    if url is None:
        url = 'https://serpapi.com/search'
        params.update({
            "engine": "google_scholar",
            "q": term,
            "hl": "en",
            "num": 20,  # Maxed out at 20
            "scisbd": scisbd,
            "as_vis": 1,
        })

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")


def next_page_url(results: dict) -> str | None:
    """Get the URL for the next page of results."""
    return results['pagination']['next']


############################## Obsolete ##############################
def query_xdd(term: str) -> dict | None:
    """Query the XDD API for snippets containing the given term."""
    url = 'https://xdd.wisc.edu/api/snippets'
    params = {
        'term': term,
        'article_limit': 1000
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")




