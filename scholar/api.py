import os
import re
import json
import requests
from time import sleep
from typing import Optional
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET
from .database import insert_serp_results

load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")
ARXIV_CATEGORY_MAP = json.load(open("scholar/arxiv_category.json"))
ARXIV_GROUP_MAP = json.load(open("scholar/arxiv_group.json"))

def get_arxiv_category_map() -> dict:
    url = 'https://arxiv.org/category_taxonomy'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    data = soup.find("div", id="category_taxonomy_list").select('h4')

    category_mapping = {}
    for record in data:
        text = str(record)
        category = re.search(r"<h4>(.*?) <span>", text).group(1)
        full_name = re.search(r"<span>\((.*?)\)</span>", text).group(1)
        category_mapping[category] = full_name
    
    return category_mapping


def get_arxiv_category(title: str) -> str:
    """Get arxiv category from title.
    
    see: https://arxiv.org/category_taxonomy
    """

    sleep(0.5)  # Avoid being blocked by arxiv (max 3 requests per second)
    url = "http://export.arxiv.org/api/query"
    payload = {"search_query": f"ti:'{title}'", "max_results": 1}
    response = requests.get(url, params=payload)

    root = ET.fromstring(response.content)
    namespaces = {
        'arxiv': 'http://arxiv.org/schemas/atom'
    }
    category = root.find(".//arxiv:primary_category", namespaces)
    if category is not None:
        category = category.attrib['term']

    if category in ARXIV_CATEGORY_MAP:
        return category


def to_group(arxiv_category: Optional[str]) -> str:
    """Convert arxiv category to group."""
    if arxiv_category is None:
        return None
    group_tag = arxiv_category.split('.')[0]
    if group_tag in ARXIV_GROUP_MAP:
        return group_tag


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

        ### TODO:  Insert Arxiv category and group
        for result in results['organic_results']:
            title = result['title']
            arxiv_category = get_arxiv_category(title)
            result['arxiv_category'] = arxiv_category
            result['arxiv_group'] = to_group(arxiv_category)

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
