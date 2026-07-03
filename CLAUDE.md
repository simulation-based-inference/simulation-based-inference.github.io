# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The website for [simulation-based-inference.org](http://simulation-based-inference.org/): a crowd-sourced, auto-updated catalog of research papers on simulation-based inference (SBI). It is a **Jekyll static site** (Bulma clean theme, deployed to GitHub Pages) fed by a **Python crawler pipeline** (`backend/`) that discovers new papers, enriches their metadata, categorizes them, and generates Jekyll posts.

## Commands

Two separate toolchains — Python for content generation, Ruby/Jekyll for the site.

**Python pipeline** (Python 3.11):
```bash
pip install -r backend/requirements.txt
python main.py                     # regenerate all posts from papers.yaml + rebuild the plot (no crawl)
python main.py --crawl             # crawl SERP for new papers, then regenerate everything
python main.py --crawl --stop-days 90   # stop crawling once results get older than N days
```
Crawling requires `SERP_API_KEY` and `OPENAI_API_KEY` in the environment (or a `.env` file — loaded via `python-dotenv`).

**Jekyll site** (Ruby 3.1+):
```bash
bundle install
bundle exec jekyll serve           # local preview
bundle exec jekyll build           # production build to _site/
```
Jekyll builds slowly with the full ~1800-post corpus. Use `python scripts/dev_delete_posts.py` to thin `_posts/`/`_misc/` down to a handful of random posts for fast local iteration — posts are disposable and can be regenerated with `python main.py`.

**Formatting:** `black` via pre-commit (`pre-commit run --all-files`). There is no automated test suite.

## Architecture

### The YAML database is the source of truth

`backend/data/papers.yaml` is the canonical store of all papers (~1800 entries). Everything in `_posts/` and `_misc/` is **generated output** — `remake_all_posts()` deletes every `.md` in those dirs and regenerates them from `papers.yaml` on every run. Never hand-edit generated posts; edit `papers.yaml` (or the data files under `backend/data/`) and regenerate. CRUD helpers live in `backend/database.py`; the `Paper` pydantic model there validates and sanitizes every field (notably `title_safe_for_jekyll`, which strips characters that would break Jekyll front-matter).

### Pipeline flow (`main.py`)

1. **Crawl** (`crawl()`): paginate the SERP API (Google Scholar) for `"simulation-based+inference"`. For each result:
   - arxiv.org hits → enrich via `query_arxiv_batch` (batch), falling back to per-id `query_arxiv` (both in `backend/api.py`, which uses `tenacity` retry/backoff because the arXiv export API rate-limits aggressively).
   - biorxiv.org hits → enrich via `query_biorxiv` (DOI lookup).
   - Dedup by title against the YAML DB → `update_paper` or `insert_paper`.
2. **Categorize** (`backend/guess_category.py`, `Guesser`): assign a `category`. Priority order — arXiv group mapping (`arxiv_group.json`) → cached/OpenAI guess. `update_manual_category_group()` re-applies categories across the whole DB so manual edits to the data files take effect.
3. **Generate posts** (`backend/post_maker.py`, `remake_all_posts()`): whitelist journals (`whitelist_journals.txt`) become `_posts/`; everything else goes to `_misc/`. Blacklisted titles and undated (year 2000) papers are skipped. Bibtex is batch-fetched from arXiv.
4. **Plot** (`backend/plot_maker.py`): build the "publications by year" Altair chart → `assets/publication_by_year.json`.

### Category resolution has three tiers (`Guesser`)

Highest to lowest priority, all under `backend/data/`:
- `category_override.json` — manual `paper_id → category` overrides; always win.
- `guess_category_inference.json` — cached OpenAI guesses per paper id (avoids re-querying).
- `guess_category_group.json` — maps raw guessed labels → canonical display categories. Edit this to rename/merge categories, then run `python main.py` to propagate.

The OpenAI model is set by `OPENAI_MODEL` in `guess_category.py`.

### Automation (`.github/workflows/`)

- `pull_paper.yml` — **Weekly pull**, Sundays 00:00 UTC. Runs `python main.py --crawl`, commits changes to `main`. Note: this push uses `GITHUB_TOKEN` and deliberately does **not** trigger the deploy workflow.
- `ci.yml` — **Deploy to Pages**. Runs on push to `main`, on manual dispatch, and on a **Monday 14:00 UTC** cron (the mechanism that actually publishes the weekly-pulled papers). Runs `python main.py` (no crawl) then `bundle exec jekyll build`.

## Jekyll specifics

- `backend/` and `main.py` are excluded from the Jekyll build (see `_config.yml` `exclude`). The Python side and the site are decoupled — they only communicate through generated files (`_posts/`, `_misc/`, `assets/publication_by_year.json`).
- Collections: `jobs` (`_jobs/`) and `misc` (`_misc/`). Papers use the `paper` layout (`_layouts/paper.html`); post front-matter template lives in `POST_TEMPLATE` in `post_maker.py`.
- Content contributions typically arrive as GitHub issues (see `.github/ISSUE_TEMPLATE/`: recommend paper, correct category, report unrelated paper, etc.).
