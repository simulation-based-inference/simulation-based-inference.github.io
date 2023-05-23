from typing import Optional, Union
from datetime import datetime, date
import yaml
from pathlib import Path
from pydantic import BaseModel, validator, Field

PAPERS_YAML = Path(__file__).parent / "papers.yaml"


def get_new_id() -> int:
    """Get a new id for a paper."""

    papers = get_papers(as_dict=True)
    if papers:
        return max([paper["id"] for paper in papers]) + 1
    return 1


class Paper(BaseModel):
    """Paper object with data validations."""

    id: int = Field(default_factory=get_new_id)
    created_at: datetime = Field(default_factory=datetime.now)
    published_on: date
    title: str
    authors: Optional[str]
    publication_info_summary: str
    link: str
    snippet: str
    journal: Optional[str]
    citation_backlink: Optional[str]
    arxiv_id: Optional[str]
    arxiv_category_tag: Optional[str]
    category: Optional[str]
    doi: Optional[str]

    # Data validations (to make sure front-end doesn't break)
    @validator("published_on")
    def published_on_must_be_past_date(cls, v):
        if not isinstance(v, date):
            raise ValueError("published_on must be a date")

        if v > date.today():
            raise ValueError("published_on must be in the past")
        return v

    @validator("title")
    def title_must_note_be_empty(cls, v):
        if v == "":
            raise ValueError("title must not be empty")
        return v

    @validator("link")
    def link_must_be_url(cls, v):
        if not v.startswith("http"):
            raise ValueError("link must be a URL")
        return v

    @validator("snippet")
    def snippet_must_not_be_empty(cls, v):
        if v == "":
            raise ValueError("snippet must not be empty")
        return v

    @validator("publication_info_summary")
    def publication_info_summary_must_not_be_empty(cls, v):
        if v == "":
            raise ValueError("publication_info_summary must not be empty")
        return v


# Create, Read, Update, Delete (CRUD) operations
def write_papers(papers: list[Union[Paper, dict]]) -> None:
    """Write the papers to the YAML database."""

    if isinstance(papers[0], Paper):
        papers = [paper.dict(exclude_none=True) for paper in papers]

    with open(PAPERS_YAML, "w") as f:
        yaml.dump(papers, f, sort_keys=False)


def get_papers(as_dict: bool = False) -> list:
    """Get all papers from the YAML database."""

    with open(PAPERS_YAML, "r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    if as_dict:
        return data
    return [Paper(**paper) for paper in data]


def get_paper(id: int) -> Paper:
    """Get a paper from the YAML database."""

    papers = get_papers()
    for paper in papers:
        if paper.id == id:
            return paper
    raise ValueError(f"Paper with id {id} not found")


def insert_paper(paper: Union[dict, Paper]) -> None:
    """Write the result to the YAML database."""

    if isinstance(paper, Paper):
        paper = paper.dict(exclude_none=True)

    papers = get_papers(as_dict=True)
    papers.append(paper)
    write_papers(papers)


def update_paper(paper: Paper) -> None:
    """Update a paper in the YAML database."""

    # It is safe to use dict models here because we are not validating
    papers = get_papers(as_dict=True)

    new_papers = []
    found = False
    for p in papers:
        if p["id"] == paper.id:
            updated = paper.dict(exclude_none=True)
            new_papers.append(updated)
            found = True
        else:
            new_papers.append(p)

    if not found:
        raise ValueError(f"Paper with id {paper.id} not found")
    write_papers(papers)


def delete_paper(paper: Paper = None, id: int = None) -> None:
    """Delete a paper from the YAML database."""

    if paper is None and id is None:
        raise ValueError("Either paper or id must be provided")

    if paper is not None and id is not None:
        raise ValueError("Only one of paper or id must be provided")

    papers = get_papers(as_dict=True)
    id = paper.id if paper else id

    new_papers = [p for p in papers if p["id"] != id]
    write_papers(new_papers)
