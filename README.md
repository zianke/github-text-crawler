# github-text-crawler
Extract documentation and commit logs from GitHub repository.

## Usage
* Setup python3 virtual environment.
```
python3 -m venv venv
source venv/bin/activate
```

* Install dependencies.
```
pip install -e .
```

* Basic usage (maximum number of requests is 60 per hour). `owner` can be username or organization.
```
python -m github-text-crawler [owner] [repo]
```

* Use GitHub API personal access token (maximum number of requests is 5000 per hour).
```
python -m github-text-crawler [owner] [repo] --token=[token]
```

* Use snapshot of commit logs.
```
python -m github-text-crawler [owner] [repo] --token=[token] --commit_logs_file=[commit_logs_file]
```

After running these commands, a commit logs file and a text data file will be generated, both in json format. The commit logs file can later be used as snapshot to reduce running time.
