import re
from scholar.database import Paper
from pathlib import Path

POST_DIR = Path("_posts/")


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to make it safe for use on Windows and Linux."""

    # Remove or replace any potentially invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*,;@]', "-", filename)

    # Remove double hyphens
    sanitized = sanitized.replace("--", "-")

    # Remove any leading or trailing whitespace characters
    sanitized = sanitized.strip()

    # If the sanitized filename is empty, provide a default name
    if not sanitized:
        sanitized = "default_filename"

    return sanitized.lower()


def make_md_post(paper: Paper) -> None:
    """Make a post for the given paper."""

    # Create file name
    pub_date = paper.published_on.strftime("%Y-%m-%d")
    hyphenated_title = paper.title.replace(" ", "-")
    file_name = sanitize_filename(f"{pub_date}-{hyphenated_title}.md")

    # Create file content
    content = f"""---
    title: "{paper.title}"
    categories:
      - paper
    tags:
      - auto
    ---
    {paper.publication_info_summary}

    {paper.snippet}

    Link to paper: [{paper.link}]({paper.link})
    """.replace(
        "    ", ""
    )

    # Write file
    with open(POST_DIR / file_name, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Markdown file created successfully: {paper.title}")


def make_all() -> None:
    papers = Paper.select()
    for paper in papers:
        make_md_post(paper)


if __name__ == "__main__":
    make_all()
