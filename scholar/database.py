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

db = SqliteDatabase("scholar/paper.db")


class Paper(Model):
    id = AutoField(primary_key=True)
    result_id = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)
    days_since_added = IntegerField()
    published_on = DateField()
    title = CharField(unique=True)
    publication_info_summary = CharField()
    link = CharField()
    snippet = CharField()

    class Meta:
        database = db


def create_tables() -> None:
    """Create the tables in the database."""
    db.connect()
    db.create_tables([Paper])
    db.close()


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

        Paper.insert(
            result_id=result["result_id"],
            published_on=datetime.datetime.now()
            - datetime.timedelta(days=days_since_added),
            title=result["title"],
            days_since_added=days_since_added,
            publication_info_summary=result["publication_info"]["summary"],
            link=result["link"],
            snippet=snippet,
        ).on_conflict_ignore().execute()

    return days_since_added
