#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import click
from .github_text_crawler import GithubTextCrawler


@click.command()
@click.argument('owner')
@click.argument('repo')
@click.option('--token')
@click.option('--commit_logs_file')
@click.option('--text_data_file')
def main(owner, repo, token, commit_logs_file, text_data_file):
    commit_logs = None
    text_data = None
    if commit_logs_file:
        commit_logs = json.load(open(commit_logs_file))
    if text_data_file:
        text_data = json.load(open(text_data_file))
    gtc = GithubTextCrawler(owner, repo, token, commit_logs, text_data)
    gtc.get_commit_logs()
    gtc.save_commit_logs('commit_log.json')


if __name__ == '__main__':
    main()
