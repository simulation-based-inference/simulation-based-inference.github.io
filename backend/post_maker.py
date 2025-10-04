import json
import re
from pathlib import Path

from backend.api import get_bibtex
from backend.database import Paper, get_papers

POST_DIR = Path("_posts/")  # Journal articles
MISC_DIR = Path("_misc/")  # Misc items from crawl

with open("backend/data/blacklist_title.txt", "r") as f:
    BLACKLIST = f.read().splitlines()

with open("backend/data/whitelist_journals.txt", "r") as f:
    WHITELIST = f.read().splitlines()

# CATEGORY is arxiv sub category (!= category in paper object)
ARXIV_CATEGORY_MAP = json.load(open("backend/data/arxiv_category.json"))


POST_TEMPLATE = """---
layout: paper
title: "{title}"
author: "{publication_info_summary}"
journal: "{journal}"
year: {year}
bibtex: |
    {bibtex}
link: "{link}"
cited_by: "{cited_by}"
hero_title: "Papers"
categories:
  - {category}
tags:
  - paper
{arxiv_extra_tag}
---
>{snippet}

"""


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to make it safe for use on Windows and Linux."""

    # Replace all symbols with spaces
    sanitized = re.sub(r"[^a-zA-Z0-9\s]", " ", filename)
    sanitized = sanitized.strip()
    sanitized = sanitized.replace(" ", "-")
    sanitized = sanitized.replace("--", "-")

    if not sanitized:
        sanitized = "default_filename"

    return sanitized.lower()[:64]


def make_md(paper: Paper, overwrite: bool, output_dir: Path) -> None:
    """Make a post for the given paper."""

    # Create file name
    pub_date = paper.published_on.strftime("%Y-%m-%d")
    clean_title = sanitize_filename(paper.title)
    file_name = f"{pub_date}-{clean_title}.md"

    # Check if file already exists
    if (output_dir / file_name).exists() and not overwrite:
        print(f"File already exists: {paper.title}")
        return

    def _make_arxiv_extra_tag(paper: Paper) -> str:
        if paper.arxiv_category_tag:
            line1 = f"  - arxiv_category:"
            line2 = f"    name: {paper.arxiv_category_tag}"
            line3 = f"    tooltip: {ARXIV_CATEGORY_MAP[paper.arxiv_category_tag]}"
            return "\n".join([line1, line2, line3])
        return ""

    # Create file content
    content = POST_TEMPLATE.format(
        title=paper.title,
        journal=paper.journal,
        year=paper.published_on.year,
        publication_info_summary=paper.publication_info_summary,
        bibtex=get_bibtex(paper.arxiv_id) if paper.arxiv_id else None,
        category=paper.category if paper.category else "Uncategorized",
        arxiv_extra_tag=_make_arxiv_extra_tag(paper),
        snippet=paper.snippet,
        link=paper.link,
        cited_by=paper.citation_backlink,
    )

    # Write file
    with open(output_dir / file_name, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Markdown file created successfully: {paper.title}")


def delete_existing_mds() -> None:
    """Delete all existing posts and misc items."""

    def _delete(dir: Path) -> None:
        existing_mds = list(dir.glob("*.md"))
        [post.unlink() for post in existing_mds if post is not None]

    _delete(POST_DIR)
    _delete(MISC_DIR)


def remake_all_posts() -> None:
    """Re-make all posts from truth (paper.yaml)."""

    # Make dir
    POST_DIR.mkdir(parents=True, exist_ok=True)
    MISC_DIR.mkdir(parents=True, exist_ok=True)

    # Delete all existing posts first (Maintain consistency with truth)
    delete_existing_mds()

    # Make all posts
    papers = get_papers()

    for paper in papers:
        # Filtering
        if paper.title in BLACKLIST:
            print(f"Paper is blacklisted: {paper.title}, skipping...")
            continue

        if (
            paper.published_on.year == 2000
        ):  # Paper without publication date will have default as 2000
            print(f"Paper is undated: {paper.title}, skipping...")
            continue

        if paper.journal not in WHITELIST:
            print(f"Paper is not in whitelist journals: {paper.title}, skipping...")
            make_md(paper, overwrite=True, output_dir=MISC_DIR)
        else:
            make_md(paper, overwrite=True, output_dir=POST_DIR)
