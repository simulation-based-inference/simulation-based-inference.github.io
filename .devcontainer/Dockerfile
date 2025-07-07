FROM ruby:3.1

EXPOSE 4000

RUN apt-get update && apt-get install -y \
    build-essential \
    nodejs \
    npm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN gem install github-pages
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
