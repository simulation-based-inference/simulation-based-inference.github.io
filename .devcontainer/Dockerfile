# GitHub Pages currently builds on Ruby 3.3.x
FROM ruby:3.3

EXPOSE 4000

# Project-specific base tooling. Common dev tools (Node.js, GitHub CLI,
# Claude Code) are provided declaratively via Features in devcontainer.json.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Jekyll / GitHub Pages toolchain
RUN gem install github-pages

# uv for the Python backend
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"
