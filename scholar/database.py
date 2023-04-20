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
    id = AutoField(primary_key=True)
    result_id = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    days_since_added = IntegerField()
    published_on = DateField()
    title = CharField(unique=True)
    publication_info_summary = CharField()
    link = CharField()
    snippet = CharField()
    arxiv_group_tag = CharField(null=True)
    arxiv_category_tag = CharField(null=True)
    citation_backlink = CharField(null=True)

    class Meta:
        database = DATABASE


def create_tables() -> None:
    """Create the tables in the database."""
    DATABASE.connect()
    DATABASE.create_tables([Paper])
    DATABASE.close()


def insert_serp_results(results: list[dict]) -> None:
    """Insert the results from the SERP API into the database.

    Args:
        results (list[dict]): The results from the SERP API.

    Returns:
        int: The number of days since the oldest paper was added.
    """

    for result in results["organic_results"]:
        _tmp = result["snippet"].split(" days ago - ")
        days_since_added = int(_tmp[0])
        snippet = _tmp[1]

        try:
            citation_backlink = result["inline_links"]["cited_by"]["link"]
        except KeyError:
            citation_backlink = None

        Paper.insert(
            result_id=result["result_id"],
            published_on=datetime.datetime.now()
            - datetime.timedelta(days=days_since_added),
            title=result["title"],
            days_since_added=days_since_added,
            publication_info_summary=result["publication_info"]["summary"],
            link=result["link"],
            snippet=snippet,
            arxiv_group_tag=result["arxiv_group"],
            arxiv_category_tag=result["arxiv_category"],
            citation_backlink=citation_backlink,
        ).on_conflict(
            conflict_target=[Paper.title],
            preserve=[Paper.arxiv_group_tag, Paper.arxiv_category_tag],
            update={Paper.citation_backlink: citation_backlink},
        ).execute()

    return days_since_added


def patch_arxiv(id: int, arxiv_category_tag: str) -> None:
    """Patch the arxiv tags for a paper.

    Args:
        id (int): The ID of the paper.
        arxiv_group_tag (str): The arxiv group tag.
        arxiv_category_tag (str): The arxiv category tag.
    """
    paper = Paper.get(Paper.id == id)
    print(paper.title)
    paper.arxiv_category_tag = arxiv_category_tag
    paper.arxiv_group_tag = arxiv_category_tag.split(".")[0]
    paper.save()
