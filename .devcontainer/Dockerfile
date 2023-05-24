FROM ruby:2.7-alpine

EXPOSE 4000
# Add Jekyll dependencies to Alpine
RUN apk update
RUN apk add --no-cache build-base gcc cmake github-cli

# Update the Ruby bundler and install Jekyll
RUN gem update bundler
RUN gem install jekyll -v 3.9.3
RUN gem update github-pages

# Install Python
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools
RUN apk add gcc musl-dev linux-headers python3-dev
RUN apk add sqlite
RUN apk add bash
