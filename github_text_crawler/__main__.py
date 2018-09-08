#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .github_text_crawler import GithubTextCrawler


def main():
    gtc = GithubTextCrawler(owner='ApolloAuto', repo='apollo')


if __name__ == '__main__':
    main()
