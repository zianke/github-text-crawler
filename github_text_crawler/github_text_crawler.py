#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import time
import base64
import requests


class RepoNotFoundError(Exception):
    """Custom exception when repo is missing."""
    pass


class CommitNotFoundError(Exception):
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

            # Check last_commit_sha existence
            if not self.check_commit_existence(last_commit_sha):
                raise CommitNotFoundError(
                    'Commit {} not found in repo {}/{}.'.format(last_commit_sha, self.owner, self.repo))

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

            # Find index of last_commit_sha
            last_commit_index = len(commit_logs) - 1
            while commit_logs[last_commit_index]['sha'] != last_commit_sha:
                last_commit_index -= 1
                assert last_commit_index >= 0

            # Discard commit logs before last_commit_sha
            commit_logs = commit_logs[:last_commit_index]

            # Convert commit_logs to full version
            commit_logs = [self.get_full_commit_log(commit_log) for commit_log in commit_logs]

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

            # Convert commit_logs to full version
            commit_logs = [self.get_full_commit_log(commit_log) for commit_log in commit_logs]

            self.commit_logs = commit_logs

    def get_full_commit_log(self, commit_log):
        print(commit_log['sha'])
        return self.get_api_json('/repos/{}/{}/commits/{}'.format(self.owner, self.repo, commit_log['sha']))

    def check_commit_existence(self, commit_sha):
        r = self.get_api_response('/repos/{}/{}/commits/{}'.format(self.owner, self.repo, commit_sha))
        if r.status_code == 200:
            return True
        else:
            return False

    def save_commit_logs(self, filename=None):
        if not filename:
            filename = '{}_{}_commit_logs.json'.format(self.owner, self.repo)
        with open(filename, 'w+') as f:
            json.dump(self.commit_logs, f, indent=4)

    def get_text_data(self):
        if len(self.commit_logs) == 0:
            raise CommitNotFoundError('Commit logs empty. Please run get_commit_logs() first.')
        if 'last_commit_sha' in self.text_data:
            last_commit_sha = self.text_data['last_commit_sha']
            self.add_commits_to_text_data(last_commit_sha)
        else:
            tree_sha = self.commit_logs[0]['commit']['tree']['sha']
            self.text_data = self.get_trees(tree_sha)
            self.add_commits_to_text_data()
            self.add_docs_to_text_data()
        self.text_data['last_commit_sha'] = self.commit_logs[0]['sha']

    def get_tree(self, tree_sha):
        tree = self.get_api_json('/repos/{}/{}/git/trees/{}'.format(self.owner, self.repo, tree_sha))
        # Remove non-text files
        tree['tree'] = list(
            filter(lambda item: item['type'] == 'tree' or item['type'] == 'blob' and self.is_doc(item['path']), tree['tree']))
        tree.update({'commits': [], 'docs': []})
        return tree

    def get_trees(self, tree_sha):
        trees = self.get_tree(tree_sha)
        for path in trees['tree']:
            if path['type'] == 'tree':
                path.update(self.get_trees(path['sha']))
        return trees

    def add_commits_to_text_data(self, last_commit_sha=None):
        last_commit_index = len(self.commit_logs)
        if last_commit_sha:
            for i, commit in enumerate(self.commit_logs):
                if commit['sha'] == last_commit_sha:
                    last_commit_index = i
                    break
            if last_commit_index == len(self.commit_logs):
                raise CommitNotFoundError('Commit {} not found in commit logs.'.format(last_commit_sha))
        for commit_index in reversed(range(last_commit_index)):
            commit = self.commit_logs[commit_index]
            filenames = [file['filename'] for file in commit['files']]
            dirnames = set()
            for filename in filenames:
                dirnames.add(os.path.dirname(filename))
            for dirname in dirnames:
                if dirname == '':
                    dirs = []
                else:
                    dirs = dirname.split('/')
                target_tree = self.text_data
                try:
                    for dir in dirs:
                        target_tree = [tree for tree in target_tree['tree'] if tree['path'] == dir]
                        if len(target_tree) != 1:
                            raise KeyError
                        target_tree = target_tree[0]
                    target_tree['commits'].append({'sha': commit['sha'], 'message': commit['commit']['message']})
                except KeyError:
                    pass

    def add_docs_to_text_data(self):
        self.add_docs_to_trees(self.text_data)

    def add_docs_to_trees(self, tree):
        if 'tree' not in tree:
            return
        docs = list(
            filter(lambda item: item['type'] == 'blob' and self.is_doc(item['path']), tree['tree']))
        docs = [self.update_doc_content(doc) for doc in docs]
        tree['docs'] = docs
        for item in tree['tree']:
            if item['type'] == 'tree':
                self.add_docs_to_trees(item)

    @staticmethod
    def is_doc(filename):
        filename = filename.lower()
        return filename.endswith('.md') or filename.endswith('.rst')

    def update_doc_content(self, doc):
        doc = {'filename': doc['path'], 'sha': doc['sha'], 'content': self.get_doc_content(doc['sha'])}
        return doc

    def get_doc_content(self, blob_sha):
        content = self.get_api_json('/repos/{}/{}/git/blobs/{}'.format(self.owner, self.repo, blob_sha))['content']
        return base64.b64decode(content).decode('utf-8')

    def save_text_data(self, filename=None):
        if not filename:
            filename = '{}_{}_text_data.json'.format(self.owner, self.repo)
        with open(filename, 'w+') as f:
            json.dump(self.text_data, f, indent=4)
