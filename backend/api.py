import datetime
import json
import logging
import os
import re
import signal
from contextlib import contextmanager
from html import escape
from time import sleep
from typing import Any, Optional

import arxiv
import requests
from arxiv2bib import arxiv2bib
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")

with open("backend/data/arxiv_group.json", "r") as f:
    ARXIV_GROUP_MAP = json.load(f)

# arxiv export API rate-limits aggressively; use long delays and many retries.
ARXIV_CLIENT = arxiv.Client(page_size=100, delay_seconds=10.0, num_retries=8)


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

@retry(wait=wait_exponential(min=2, max=60), stop=stop_after_attempt(5))
def get_bibtex(arxiv_id: str) -> Optional[str]:
    """Fetch BibTeX entry for a given arXiv ID."""

    bibtex = arxiv2bib([arxiv_id])
    # Escape HTML safely instead of manual replacements
    return escape(bibtex[0].bibtex()).replace("\n", "<br>")


@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(5))
def _fetch_bibtex_chunk(arxiv_ids: list[str]) -> dict[str, str]:
    """Fetch BibTeX entries for a chunk of arXiv IDs (max 100)."""
    results = arxiv2bib(arxiv_ids)
    bibtex_map = {}
    for arxiv_id, entry in zip(arxiv_ids, results):
        try:
            bibtex_map[arxiv_id] = escape(entry.bibtex()).replace("\n", "<br>")
        except Exception:
            bibtex_map[arxiv_id] = "N/A"
    return bibtex_map


def get_bibtex_batch(arxiv_ids: list[str], chunk_size: int = 100) -> dict[str, str]:
    """Fetch BibTeX entries for multiple arXiv IDs in batches of chunk_size.

    Returns a dict mapping arxiv_id to its formatted bibtex string.
    """
    if not arxiv_ids:
        return {}

    bibtex_map = {}
    for i in range(0, len(arxiv_ids), chunk_size):
        chunk = arxiv_ids[i:i + chunk_size]
        try:
            bibtex_map.update(_fetch_bibtex_chunk(chunk))
        except Exception:
            logging.warning(f"Failed to fetch bibtex for chunk starting at index {i}")
            for arxiv_id in chunk:
                bibtex_map[arxiv_id] = "N/A"
    return bibtex_map


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


@retry(
    retry=retry_if_exception_type(arxiv.HTTPError),
    wait=wait_exponential(min=5, max=120),
    stop=stop_after_attempt(5),
    reraise=True,
)
def query_arxiv(arxiv_id: str) -> dict[str, Any] | None:
    """Query arxiv for a paper with the given title."""
    search = arxiv.Search(id_list=[arxiv_id], max_results=1)

    try:
        result = next(ARXIV_CLIENT.results(search))
    except StopIteration:
        return None
    except arxiv.HTTPError:
        raise
    except Exception as e:
        logging.warning(f"arxiv query failed for {arxiv_id}: {e}")
        return None

    return {
        "authors": ", ".join([str(author) for author in result.authors]),
        "doi": result.doi,
        "arxiv_category_tag": result.primary_category,
        "category": to_category(result.primary_category),
        "published_on": result.published.date(),
        "title": result.title,
    }


class _ArxivChunkTimeout(Exception):
    """Raised when a single arxiv batch chunk exceeds its wall-clock budget."""


@contextmanager
def _chunk_timeout(seconds: int):
    """Bound a block of code with a SIGALRM-based wall-clock timeout.

    The arxiv Python library passes no timeout to urllib, so a single
    misbehaving request can hang indefinitely. SIGALRM works on Linux
    (our CI target) and from the main thread; if either condition isn't
    met we silently skip the timeout rather than fail.
    """

    def handler(signum, frame):
        raise _ArxivChunkTimeout(f"chunk exceeded {seconds}s")

    try:
        old_handler = signal.signal(signal.SIGALRM, handler)
    except (ValueError, AttributeError):
        yield
        return
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def _arxiv_result_to_dict(result) -> dict[str, Any]:
    return {
        "authors": ", ".join(str(author) for author in result.authors),
        "doi": result.doi,
        "arxiv_category_tag": result.primary_category,
        "category": to_category(result.primary_category),
        "published_on": result.published.date(),
        "title": result.title,
    }


def query_arxiv_batch(
    arxiv_ids: list[str],
    chunk_size: int = 25,
    chunk_timeout_seconds: int = 120,
) -> dict[str, dict[str, Any]]:
    """Query arxiv for multiple papers via chunked id_list requests.

    Small chunks (default 25) avoid the arxiv library's tendency to silently
    drop IDs from large bulk id_list queries. Each chunk is bounded by
    chunk_timeout_seconds. On any chunk failure (HTTP, timeout, parse) we
    log and move on — IDs that arxiv drops or that fail outright are simply
    absent from the returned dict, so the caller can fall back to per-id.
    """
    if not arxiv_ids:
        return {}

    seen: set[str] = set()
    deduped: list[str] = []
    for aid in arxiv_ids:
        if aid and aid not in seen:
            seen.add(aid)
            deduped.append(aid)

    results: dict[str, dict[str, Any]] = {}
    for i in range(0, len(deduped), chunk_size):
        chunk = deduped[i:i + chunk_size]
        chunk_idx = i // chunk_size
        try:
            with _chunk_timeout(chunk_timeout_seconds):
                search = arxiv.Search(id_list=chunk, max_results=len(chunk))
                for result in ARXIV_CLIENT.results(search):
                    aid = re.sub(r"v\d+$", "", result.entry_id.split("/")[-1])
                    results[aid] = _arxiv_result_to_dict(result)
        except _ArxivChunkTimeout:
            logging.warning(
                f"arxiv batch chunk {chunk_idx} timed out after "
                f"{chunk_timeout_seconds}s; {len(chunk)} ids will fall back to per-id"
            )
        except arxiv.HTTPError as e:
            logging.warning(
                f"arxiv batch chunk {chunk_idx} HTTPError ({e}); "
                f"{len(chunk)} ids will fall back to per-id"
            )
        except Exception as e:
            logging.warning(
                f"arxiv batch chunk {chunk_idx} failed: {e}; "
                f"{len(chunk)} ids will fall back to per-id"
            )
    return results


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
