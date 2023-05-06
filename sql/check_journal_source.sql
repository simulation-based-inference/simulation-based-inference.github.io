-- SQLite
-- SELECT id, publication_info_summary, journal FROM paper;


SELECT link, category, doi FROM paper WHERE journal = 'biorxiv.org';