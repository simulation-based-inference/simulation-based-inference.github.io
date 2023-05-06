-- SQLite
SELECT id, title, arxiv_group_tag, arxiv_category_tag FROM paper WHERE arxiv_category_tag ISNULL;