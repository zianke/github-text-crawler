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
            r = self.get_api_response('/repos/{}/{}'.format(self.owner, self.repo))
            if r.status_code == 200:
                return True
        return False

    def get_api_response(self, endpoint):
        url = 'https://api.github.com{}'.format(endpoint)
        while True:
            r = requests.get(url, headers=self.headers)
            # If maximum number of requests is exceeded, sleep until next rate limit window
            if r.status_code == 403 and int(r.headers['X-RateLimit-Remaining']) == 0:
                print('Exceed maximum number of requests. Sleeping...')
                reset_time = int(r.headers['X-RateLimit-Reset'])
                while time.time() < reset_time:
                    print('{} seconds left.'.format(reset_time - int(time.time())))
                    time.sleep(70)
            else:
                break
        return r

    def get_api_json(self, endpoint):
        r = self.get_api_response(endpoint)
        return r.json()

    def get_commit_logs(self):
        if len(self.commit_logs) > 0:
            # If self.commit_logs not empty, specify last_commit_date
            last_commit_sha = self.commit_logs[0]['sha']
            last_commit_date = self.commit_logs[0]['commit']['committer']['date']

            # Get first 100 commit logs since last_commit_date
            commit_logs = list(self.get_api_json(
                '/repos/{}/{}/commits?per_page=100&since={}'.format(self.owner, self.repo, last_commit_date)))
            if len(commit_logs) == 100:
                # Get the rest commit logs since last_commit_date
                while True:
                    sha = commit_logs[-1]['sha']
                    new_commit_logs = list(self.get_api_json(
                        '/repos/{}/{}/commits?per_page=100&since={}&sha={}'.format(self.owner, self.repo, last_commit_date,
                                                                                   sha)))[1:]
                    commit_logs += new_commit_logs
                    if len(new_commit_logs) < 99:
                        break

            # Find index of last_commit_sha and prepend commit logs before this index
            last_commit_index = len(commit_logs) - 1
            while commit_logs[last_commit_index]['sha'] != last_commit_sha:
                last_commit_index -= 1
                assert last_commit_index >= 0
            self.commit_logs = commit_logs[:last_commit_index] + self.commit_logs
        else:
            # Get first 100 commit logs
            commit_logs = list(self.get_api_json(
                '/repos/{}/{}/commits?per_page=100'.format(self.owner, self.repo)))
            if len(commit_logs) == 100:
                # Get the rest commit logs
                while True:
                    sha = commit_logs[-1]['sha']
                    new_commit_logs = list(self.get_api_json(
                        '/repos/{}/{}/commits?per_page=100&sha={}'.format(self.owner, self.repo, sha)))[1:]
                    commit_logs += new_commit_logs
                    print(len(commit_logs))
                    if len(new_commit_logs) < 99:
                        break
            self.commit_logs = commit_logs

    def save_commit_logs(self, filename):
        with open(filename, 'w+') as f:
            json.dump(self.commit_logs, f, indent=4)
