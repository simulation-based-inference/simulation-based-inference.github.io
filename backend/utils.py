import re


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to make it safe for use on Windows and Linux."""

    # Replace all symbols with spaces
    sanitized = re.sub(r"[^a-zA-Z0-9\s]", " ", filename)
    sanitized = sanitized.strip()
    sanitized = sanitized.replace(" ", "-")
    sanitized = sanitized.replace("--", "-")

    if not sanitized:
        sanitized = "default_filename"

    return sanitized.lower()[:64]
