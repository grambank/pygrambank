"""

"""
import re
import pathlib
import textwrap
from urllib.request import urlretrieve

import dateutil.parser
from bs4 import BeautifulSoup as bs
from markdown import markdown
from clldutils import jsonlib
from clldutils.clilib import Table, add_format
from termcolor import colored

# FIXME:
# - inline images
# - render threads as html


def register(parser):
    add_format(parser, 'simple')
    parser.add_argument('--id', help='Issue ID', default=None)


# Redirect links:
# wiki:
# https://github.com/glottobank/Grambank/wiki/Responsibilities-for-parties-involved-in-GramBank
# issues:
# https://github.com/glottobank/Grambank/issues/114


class Base:
    def __init__(self, d):
        self.d = d
        self.body = self.d['body'].strip()

    @property
    def stripped_body(self):
        return '\n'.join([line for line in self.body.split('\n') if not line.startswith('> ')]).strip()

    @property
    def user(self):
        return self.d['user']['login']

    @property
    def created(self):
        return dateutil.parser.isoparse(self.d['created_at'])

    @property
    def html(self):
        return markdown(self.d['body'])

    def iter_urls(self):
        for m in re.finditer('(?P<url>http(s)?://[^\s\)]+)', self.stripped_body):
            yield m.group('url')

    def iter_issue_links(self):
        for m in re.finditer('(?P<url>#[0-9]+)', self.stripped_body):
            yield m.group('url')

    def iter_links(self):
        for link in bs(self.html, 'html5lib').find_all('a'):
            yield(link['href'], link.text)

    def iter_images(self):
        for link in bs(self.html, 'html5lib').find_all('img'):
            yield link['src']


class Comment(Base):
    pass


class Issue(Base):
    def __init__(self, d, comments):
        Base.__init__(self, d)
        self._comments = comments
        assert self.d['comments'] == len(self._comments), '{}: {} vs {}'.format(self.d['number'], self.d['comments'], len(self._comments))
        self.id = self.d['number']

    @property
    def title(self):
        return self.d['title']

    @property
    def coding_problem(self):
        for label in self.d['labels']:
            if label['name'] == 'coding problem':
                return True
        return False

    @property
    def comments(self):
        return [Comment(comment) for comment in self._comments]


def main(issues):
    for issue in issues:
        issue = Issue(issue)
        if issue.coding_problem:
            print(issue.d['title'])
            #for href, label in issue.iter_links():
            #    print('- [{}]({})'.format(label, href))
            #for href in issue.iter_images():
            #    print('- {}'.format(href))
            #    urlretrieve(href, str(assets / href.split('/')[-1]))


def run(args):
    issues = jsonlib.load(args.repos.path('archived_discussions', 'issues.json'))
    comments = jsonlib.load(args.repos.path('archived_discussions', 'comments.json'))

    if args.id:
        issue = Issue({str(i['number']): i for i in issues}[args.id], comments.get(args.id, []))
        print(colored('{0.created} {0.user}'.format(issue), 'green'))
        print(colored(issue.title, attrs={'bold', 'underline'}))
        print('')
        print(issue.body)
        for comment in issue.comments:
            print(colored('\n    {0.created} {0.user}'.format(comment), 'green'))
            for line in comment.stripped_body.split('\n'):
                print('    ' + line)
        return

    with Table(args, 'ID', 'Title', 'User', 'Comments') as t:
        for issue in issues:
            issue = Issue(issue, comments.get(str(issue['number']), []))
            if not issue.coding_problem:
                continue
            for c in issue.comments:
                for url in c.iter_urls():
                    print(url)

            #t.append([
            #    issue.id,
            #    textwrap.shorten(issue.title, 50, placeholder=' […]'),
            #    issue.user,
            #    len(issue.comments)])
