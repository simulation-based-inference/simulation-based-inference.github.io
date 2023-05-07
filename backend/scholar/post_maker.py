import re
import json
from pathlib import Path
from scholar.api import get_bibtex
from scholar.database import Paper, get_papers

POST_DIR = Path("_posts/")

with open("backend/scholar/blacklist.txt", "r") as f:
    BLACKLIST = f.read().splitlines()

with open("scholar/whitelist_journals.txt", "r") as f:
    WHITELIST_JOURNALS = f.read().splitlines()

# CATEGORY is arxiv sub category (!= category in paper object)
ARXIV_CATEGORY_MAP = json.load(open("scholar/arxiv_category.json"))


POST_TEMPLATE = """---
layout: paper
title: "{title}"
author: "{publication_info_summary}"
image: "/assets/img/SBI-icon-192x192.png"
bibtex: "{bibtex}"
hero_title: "Papers"
categories:
  - {category}
tags:
  - paper
{arxiv_extra_tag}
---
>{snippet}

{link}

{cited_by}
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


def make_md_post(paper: Paper, overwrite: bool) -> None:
    """Make a post for the given paper."""

    # Check if paper is blacklisted
    if paper.title in BLACKLIST:
        print(f"Paper is blacklisted: {paper.title}, skipping...")
        return

    if paper.journal not in WHITELIST_JOURNALS:
        print(f"Paper is not in whitelist journals: {paper.title}, skipping...")
        return

    if (
        paper.published_on.year == 2000
    ):  # Paper without publication date will have default as 2000
        print(f"Paper is undated: {paper.title}, skipping...")
        return

    # Create file name
    pub_date = paper.published_on.strftime("%Y-%m-%d")
    clean_title = sanitize_filename(paper.title)
    file_name = f"{pub_date}-{clean_title}.md"

    # Check if file already exists
    if (POST_DIR / file_name).exists() and not overwrite:
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
        publication_info_summary=paper.publication_info_summary,
        bibtex=get_bibtex(paper.arxiv_id) if paper.arxiv_id else None,
        category=paper.category if paper.category else "Uncategorized",
        arxiv_extra_tag=_make_arxiv_extra_tag(paper),
        snippet=paper.snippet,
        link=f"Link to paper: [{paper.link}]({paper.link})",
        cited_by=f"[cited by]({paper.citation_backlink})"
        if paper.citation_backlink
        else "",
    )

    # Write file
    with open(POST_DIR / file_name, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Markdown file created successfully: {paper.title}")


def remake_all_posts() -> None:
    """Re-make all posts from truth (paper.yaml)."""

    # Delete all existing posts first (Maintain consistency with truth)
    for post in POST_DIR.glob("*.md"):
        post.unlink()

    # Make all posts
    papers = get_papers()
    for paper in papers:
        make_md_post(paper, overwrite=True)
