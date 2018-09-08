#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
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
        # Use OAuth2 token if provided
        if self.token:
            self.headers = {'Authorization': 'token {}'.format(self.token)}
        else:
            self.headers = None
        self.commit_logs = commit_logs if commit_logs else []
        self.text_data = text_data if text_data else {}
        if not self.check_repo_existence():
            raise RepoNotFoundError('Repo {}/{} is invalid.'.format(self.owner, self.repo))

    def check_repo_existence(self):
        if self.owner and self.repo:
            r = self.get_response('/repos/{}/{}'.format(self.owner, self.repo))
            print(r)
            if r.status_code == 200:
                return True
        return False

    def get_response(self, endpoint):
        url = 'https://api.github.com{}'.format(endpoint)
        while True:
            r = requests.get(url, headers=self.headers)
            # If maximum number of requests is exceeded, sleep until next rate limit window
            if r.status_code == 403:
                print('Exceed maximum number of requests. Sleeping...')
                reset_time = int(r.headers['X-RateLimit-Reset'])
                while time.time() < reset_time:
                    print('{} seconds left.'.format(reset_time - int(time.time())))
                    time.sleep(70)
            else:
                break
        return r

    def get_api_json(self, endpoint):
        r = self.get_response(endpoint)
        print(r.headers)
        return r.json

    def get_commit_logs(self):
        pass

    def save_commit_logs(self, filename):
        with open(filename, 'w+') as f:
            json.dump(self.commit_logs, f)
