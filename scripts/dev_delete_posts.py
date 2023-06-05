from pathlib import Path
import random


def main() -> None:
    """Delete all posts in _post folder except n random posts for testing.

    Problem: Jekyll build is too slow for large number of posts.
    Solution: Delete all posts except 50 random posts for testing.
    Note: This script will not delete data in the YAML data file, so the posts can be recovered with `backend.scholar.post_maker.remake_all_posts()`
    """
    POST_DIR = Path("_posts/")
    MISC_DIR = Path("_misc/")

    def _keep(dir: Path, n: int) -> None:
        existing_mds = list(dir.glob("*.md"))
        random.shuffle(existing_mds)
        [post.unlink() for post in existing_mds[n:]]

    _keep(POST_DIR, n=20)
    _keep(MISC_DIR, n=3)


if __name__ == "__main__":
    main()
