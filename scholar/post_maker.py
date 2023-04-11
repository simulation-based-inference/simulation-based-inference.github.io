from scholar.database import Paper
from pathlib import Path

POST_DIR = Path("_posts/")


def make_md_post(paper: Paper) -> None:
    """Make a post for the given paper."""

    # Create file name
    pub_date = paper.published_on.strftime("%Y-%m-%d")
    hyphenated_title = paper.title.replace(" ", "-").replace(":", "").lower()
    file_name = f"{pub_date}-{hyphenated_title}.md"

    # Create file content
    content = f"""
    ---
    title: {paper.title}
    categories:
    - paper
    tags:
    - auto
    ---
    {paper.publication_info_summary}
    {paper.snippet}
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
