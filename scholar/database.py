from peewee import Model, SqliteDatabase, CharField

db = SqliteDatabase('scholar/paper.db')




class Paper(Model):
    result_id = CharField(primary_key=True)
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


def insert_serp_results(results: dict) -> None:
    """Insert the results from the SERP API into the database."""

    for result in results['organic_results']:
        Paper.insert(
            result_id=result['result_id'],
            title=result['title'],
            publication_info_summary=result['publication_info']['summary'],
            link=result['link'],
            snippet=result['snippet'],
        ).on_conflict_replace().execute()
