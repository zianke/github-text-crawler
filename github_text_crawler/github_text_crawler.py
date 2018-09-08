#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests


class RepoNotFoundError(Exception):
    """Custom exception when repo is missing."""
    pass


class GithubTextCrawler(object):
    def __init__(self,
                 owner='',
                 repo='',
                 token=None,
                 commit_logs=None,
                 text_data=None):
        self.owner = owner
        self.repo = repo
        self.token = token
        self.commit_logs = commit_logs
        self.text_data = text_data
        if not self.check_repo_existence():
            raise RepoNotFoundError('Repo {}/{} is invalid.'.format(self.owner, self.repo))

    def check_repo_existence(self):
        if self.owner and self.repo:
            url = 'https://api.github.com/repos/{}/{}'.format(self.owner, self.repo)
            headers = {}
            # Use OAuth2 token if provided
            if self.token:
                headers = {'Authorization': 'token {}'.format(self.token)}
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                return True
        return False
