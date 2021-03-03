"""
Download issues and associated comments from GitHub for glottobank/Grambank
"""
import os
import re

import requests
from requests.auth import HTTPBasicAuth
from clldutils import jsonlib

API = "https://api.github.com"
REPOS = "glottobank/Grambank"
LINK_PATTERN = re.compile(r'<(?P<url>[^>]+)>; rel=\"(?P<rel>[a-z]+)\"')


def register(parser):  # pragma: no cover
    parser.add_argument(
        '--user', default='xrotwang', help='GitHub user name')
    parser.add_argument(
        '--token', default=os.environ.get('GITHUB_TOKEN'), help='GitHub access token')


def run(args):  # pragma: no cover
    auth = HTTPBasicAuth(args.user, args.token)
    issues = list(iteritems(auth, '/repos/{0}/issues'.format(REPOS), state='all'))
    jsonlib.dump(issues, args.repos.issues_path, indent=4)

    res = {}
    for issue in issues:
        if issue['comments']:
            res[issue['number']] = list(iteritems(auth, issue['comments_url']))

    jsonlib.dump(res, args.repos.comments_path, indent=4)


def req(auth, url, **params):  # pragma: no cover
    if url.startswith('/'):
        url = API + url
    res = requests.get(url, params=params, auth=auth)
    links = {}
    for link in res.headers.get('Link', '').split(', '):
        match = LINK_PATTERN.match(link)
        if link:
            links[match.group('rel')] = match.group('url')
    return res.json(), links


def iteritems(auth, path, **params):  # pragma: no cover
    items, links = req(auth, path, **params)
    for item in items:
        yield item
    while links.get('next'):
        items, links = req(auth, links['next'])
        for item in items:
            yield item
