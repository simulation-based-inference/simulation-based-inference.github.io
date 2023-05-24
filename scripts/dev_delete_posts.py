from pathlib import Path
import random


def main(n=30) -> None:
    """Delete all posts in _post folder except n random posts for testing.

    Problem: Jekyll build is too slow for large number of posts.
    Solution: Delete all posts except 50 random posts for testing.
    Note: This script will not delete data in the YAML data file, so the posts can be recovered with `backend.scholar.post_maker.remake_all_posts()`
    """

    POST_DIR = Path("_posts/")
    posts = list(POST_DIR.glob("*.md"))
    random.shuffle(posts)
    for post in posts[n:]:
        post.unlink()


if __name__ == "__main__":
    main()
