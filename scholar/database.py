import datetime
from peewee import (
    Model,
    SqliteDatabase,
    CharField,
    DateTimeField,
    DateField,
    AutoField,
    IntegerField,
)

DATABASE = SqliteDatabase("scholar/paper.db")


class Paper(Model):
    # SERP API fields
    id = AutoField(primary_key=True)
    result_id = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    published_on = DateField()
    title = CharField(unique=True)
    publication_info_summary = CharField()
    journal = CharField(null=True)
    link = CharField()
    snippet = CharField()
    citation_backlink = CharField(null=True)
    # Arxiv fields
    arxiv_id = CharField(null=True)
    arxiv_category_tag = CharField(null=True)
    category = CharField(null=True)
    authors = CharField(null=True)
    doi = CharField(null=True)

    class Meta:
        database = DATABASE


def create_tables() -> None:
    """Create the tables in the database."""
    DATABASE.connect()
    DATABASE.create_tables([Paper])
    DATABASE.close()


def insert_result(result: dict) -> None:
    """Insert the results from the SERP API into the database.

    Args:
        results: The a formatted result from the SERP API.

    Returns:
        int: The number of days since the oldest paper was added.
    """

    Paper.insert(**result).on_conflict(
        conflict_target=[Paper.title],
        preserve=[
            Paper.arxiv_category_tag,
            Paper.published_on,
        ],
        update={
            Paper.citation_backlink: result["citation_backlink"],
        },
    ).execute()


def patch_arxiv(id: int, arxiv_category_tag: str) -> None:
    """Patch the arxiv tags for a paper.

    Args:
        id (int): The ID of the paper.
        arxiv_category_tag (str): The arxiv category tag.
    """
    paper = Paper.get(Paper.id == id)
    print(paper.title)
    paper.arxiv_category_tag = arxiv_category_tag
    paper.save()
