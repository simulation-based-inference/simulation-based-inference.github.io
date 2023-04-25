import re
from pathlib import Path
from scholar.database import Paper
from scholar.api import ARXIV_GROUP_MAP

POST_DIR = Path("_posts/")

with open("scholar/blacklist.txt", "r") as f:
    BLACKLIST = f.read().splitlines()


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

    # Create file name
    pub_date = paper.published_on.strftime("%Y-%m-%d")
    clean_title = sanitize_filename(paper.title)
    file_name = f"{pub_date}-{clean_title}.md"

    # Check if file already exists
    if (POST_DIR / file_name).exists() and not overwrite:
        print(f"File already exists: {paper.title}")
        return

    if paper.arxiv_group_tag:
        category = ARXIV_GROUP_MAP[paper.arxiv_group_tag]
    else:
        category = "Uncategorized"

    if paper.citation_backlink:
        cited_by = f"[cited by]({paper.citation_backlink})"
    else:
        cited_by = ""

    # Create file content
    content = f"""---
    title: "{paper.title}"
    hero_title: "Papers"
    categories:
      - {category}
    tags:
      - paper
    ---
    {paper.publication_info_summary}

    {cited_by}

    >{paper.snippet}

    Link to paper: [{paper.link}]({paper.link})
    """.replace(
        "    ", ""
    )

    # Write file
    with open(POST_DIR / file_name, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Markdown file created successfully: {paper.title}")


def make_all(overwrite: bool = False) -> None:
    papers = Paper.select()
    for paper in papers:
        make_md_post(paper, overwrite=overwrite)


if __name__ == "__main__":
    make_all()
