FROM ruby:2.7-alpine

EXPOSE 4000
# Add Jekyll dependencies to Alpine
RUN apk update
RUN apk add --no-cache build-base gcc cmake github-cli

# Update the Ruby bundler and install Jekyll
RUN gem update bundler 
RUN gem install jekyll -v 3.9.3
RUN gem update github-pages