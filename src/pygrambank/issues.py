import re

import dateutil.parser
from markdown import markdown
from bs4 import BeautifulSoup as bs

# Redirect links:
# wiki:
# https://github.com/glottobank/Grambank/wiki/Responsibilities-for-parties-involved-in-GramBank
# issues:
# https://github.com/glottobank/Grambank/issues/114
# FIXME:
# - inline images
# - render threads as html

__all__ = ['Issue']


class Base:
    def __init__(self, d):
        self.d = d
        self.body = self.d['body'].strip()

    @property
    def stripped_body(self):
        return '\n'.join([
            line for line in self.body.split('\n') if not line.startswith('> ')]).strip()

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
        for m in re.finditer(r'(?P<url>http(s)?://[^\s)]+)', self.stripped_body):
            yield m.group('url')

    def iter_issue_links(self):
        for m in re.finditer('(?P<url>#[0-9]+)', self.stripped_body):
            yield m.group('url')

    def iter_links(self):
        for link in bs(self.html, 'html5lib').find_all('a'):
            yield link['href'], link.text

    def iter_images(self):
        for link in bs(self.html, 'html5lib').find_all('img'):
            yield link['src'], link.get('alt')


class Comment(Base):
    pass


class Issue(Base):
    def __init__(self, d, comments):
        Base.__init__(self, d)
        self._comments = comments
        assert self.d['comments'] == len(self._comments), '{}: {} vs {}'.format(
            self.d['number'], self.d['comments'], len(self._comments))
        self.id = self.d['number']

    @property
    def title(self):
        return self.d['title']

    @property
    def coding_problem(self):
        for label in self.d['labels']:
            if label['name'] == 'coding problem':
                return True
        return False  # pragma: no cover

    @property
    def comments(self):
        return [Comment(comment) for comment in self._comments]
