import datetime
import json
import logging
import os
import re
from html import escape
from time import sleep
from typing import Any, Optional

import arxiv
import requests
from arxiv2bib import arxiv2bib
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt

load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")

with open("backend/data/arxiv_group.json", "r") as f:
    ARXIV_GROUP_MAP = json.load(f)


def timeout(func, duration=0.5):
    """Delay the execution of a function to prevent blockage."""

    def wrapper(*args, **kwargs):
        sleep(duration)
        return func(*args, **kwargs)

    return wrapper


def get_arxiv_category_map() -> dict:
    """Get the arxiv category mapping."""

    url = "https://arxiv.org/category_taxonomy"
    response = requests.get(url)
    soup = BeautifulSoup(str(response.content), "html.parser")
    data = soup.find("div", id="category_taxonomy_list").select("h4")  # type: ignore

    category_mapping = {}
    for record in data:
        text = str(record)
        category = re.search(r"<h4>(.*?) <span>", text).group(1)  # type: ignore
        full_name = re.search(r"<span>\((.*?)\)</span>", text).group(1)   # type: ignore
        category_mapping[category] = full_name

    return category_mapping

@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(5))
def get_bibtex(arxiv_id: str) -> Optional[str]:
    """Fetch BibTeX entry for a given arXiv ID."""

    bibtex = arxiv2bib([arxiv_id])
    # Escape HTML safely instead of manual replacements
    return escape(bibtex[0].bibtex()).replace("\n", "<br>")


def to_category(arxiv_category: Optional[str]) -> str | None:
    """Convert arxiv category to arxiv group (aka category in frontend)."""

    if arxiv_category is None:
        return None
    group_tag = arxiv_category.split(".")[0]
    return ARXIV_GROUP_MAP.get(group_tag, None)


def to_doi(biorxiv_link: str) -> str:
    """Convert biorxiv link to doi."""

    if biorxiv_link is None:
        return None
    doi = biorxiv_link.replace("https://www.biorxiv.org/content/", "")
    doi = doi.replace("v1", "").replace("v2", "").replace("v3", "")
    doi = doi.replace(".abstract", "").replace(".full", "").replace(".short", "")
    return doi


@timeout
def query_biorxiv(doi: str) -> dict | None:
    """Query biorxiv for a paper with the given doi."""

    url = f"https://api.biorxiv.org/details/biorxiv/{doi}"
    response = requests.get(url)

    if response.status_code == 200:
        try:
            data = response.json()["collection"][0]
        except (KeyError, IndexError):
            logging.info(f"Failed to fetch biorxiv data for DOI {doi}")
            return None
        return {
            "authors": data["authors"],
            "doi": data["doi"],
            "category": data["category"].capitalize(),
        }


@timeout
def query_arxiv(arxiv_id: str) -> dict[str, Any] | None:
    """Query arxiv for a paper with the given title."""
    search = arxiv.Search(id_list=[arxiv_id], max_results=1)

    try:
        result = next(search.results())
    except StopIteration:
        return None

    return {
        "authors": ", ".join([str(author) for author in result.authors]),
        "doi": result.doi,
        "arxiv_category_tag": result.primary_category,
        "category": to_category(result.primary_category),
        "published_on": result.published.date(),
        "title": result.title,
    }


def format_backlink(url: str) -> str | None:
    """Format citation backlink obtained from SERP API."""

    if not url:
        return None

    # Non-google scholar link returns as is
    if "scholar.google" not in url:
        return url

    # Google scholar link remove junks
    splitted = url.split("&as_sdt")
    return splitted[0]


def format_serp_result(result: dict) -> dict:
    """Format the SERP API results."""

    publication_info_summary = result["publication_info"]["summary"]

    # Determine whether the result is from journal or not
    summary_split = publication_info_summary.split(" - ")
    journal = summary_split[2] if len(summary_split) == 3 else None

    logging.debug(f"{publication_info_summary=}")

    try:
        matches = re.findall(r"\d{4}", summary_split[1])
        year_of_publication = int(matches[-1])
    except IndexError:
        year_of_publication = 0

    if " days ago - " in result["snippet"]:
        _tmp = result["snippet"].split(" days ago - ")
        snippet = _tmp[1]
        days_since_added = int(_tmp[0])
        published_on = datetime.datetime.now() - datetime.timedelta(
            days=days_since_added
        )
        published_on = published_on.date()
    else:
        snippet = result["snippet"]
        published_on = datetime.date(year_of_publication, 1, 1)

    try:
        citation_backlink = result["inline_links"]["cited_by"]["link"]
        citation_backlink = format_backlink(citation_backlink)
    except KeyError:
        citation_backlink = None

    if journal == "arxiv.org":
        arxiv_id = result["link"].split("/")[-1][:10]
    else:
        arxiv_id = None

    return {
        "published_on": published_on,
        "title": result["title"],
        "publication_info_summary": publication_info_summary,
        "journal": journal,
        "doi": to_doi(result["link"]),
        "link": result["link"],
        "snippet": snippet,
        "citation_backlink": citation_backlink,
        "arxiv_id": arxiv_id,
    }


def query_serp(
    url: str | None = None,
    term: str | None = None,
    more_results: bool = False,
    historical: bool = False,
) -> Optional[dict]:
    """Query the SERP API for snippets containing the given term.

    Args:
        url (str): API URL. If None, use the default.
        term (str): The term to search for.
        more_results (bool): If true search in everything instead of abstract.
        historical (bool): If true, search by relevant since year 2000.
    """
    params = {"api_key": SERP_API_KEY}
    scisbd = 2 if more_results else 1  # 1 = abstract, 2 = everything

    if url is None:
        url = "https://serpapi.com/search"

    params |= {
        "engine": "google_scholar",
        "q": term,
        "hl": "en",
        "num": 20,   # capped at 20 by Google Scholar
        "scisbd": scisbd,
        "as_vis": 1,
        # "as_rr": 1,  # Reviewed articles only (broken on Google Scholar as of 2023-06-02)
    }
    if historical:
        params.pop("scisbd")
        params.update({"as_ylo": 2000})

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        data["formatted_results"] = [
            format_serp_result(result) for result in data["organic_results"]
        ]
        return data
    else:
        print(
            f"Request failed with status code {response.status_code}: {response.text}"
        )
