-- SQLite

SELECT id, title, published_on, arxiv_id
FROM paper
WHERE title LIKE '%spatial random field models%'
ORDER BY published_on ASC;