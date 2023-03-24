import re
import collections

import attr
from clldutils.markup import iter_markdown_tables

PHOTO_URI = 'https://glottobank.org/photos/{Photo}'
ROLES = [
    'Project leader',
    'Project coordinator',
    'Database manager',
    'Patron',
    'Node leader',
    'Coder',
    'Methods-team',
    'Senior advisor',
]


def parse_photo(s):
    match = re.search(r'src="(?P<url>[^"]+)"', s)
    if match:
        return match.group('url').split('/')[-1]


def parse_roles(s):
    return [r.strip() for r in s.split(',') if r.strip()]


def valid_roles(instance, attribute, value):
    validator = attr.validators.in_(ROLES)
    for vv in value:
        validator(instance, attribute, vv)


@attr.s
class Contributor(object):
    id = attr.ib()
    last_name = attr.ib()
    first_name = attr.ib()
    contribution = attr.ib(
        converter=parse_roles,
        validator=valid_roles,
        default='Coder')
    node = attr.ib(default='')
    status = attr.ib(default='')
    language_competence = attr.ib(default='')
    github_username = attr.ib(default='')
    email = attr.ib(default='')
    photo = attr.ib(converter=parse_photo, default='')
    bio = attr.ib(default='')
    should_be_included_despite_no_coding = attr.ib(default=False)

    @property
    def name(self):
        return '{0.first_name} {0.last_name}'.format(self)

    @property
    def roles(self):
        return sorted(self.contribution, key=lambda r: ROLES.index(r))


def norm_header(s):
    return s.lower().replace(' ', '_').replace('-', '_')


class Contributors(list):
    @classmethod
    def from_md(cls, fname):
        fields = {f.name for f in attr.fields(Contributor)}
        header, rows = next(iter_markdown_tables(fname.read_text(encoding='utf8')))
        header = [norm_header(c) for c in header]
        rows = [
            Contributor(**{k: v for k, v in zip(header, row) if k in fields})
            for row in rows]
        byid = collections.Counter(r.id for r in rows)
        if byid.most_common(1)[0][1] > 1:  # pragma: no cover
            raise ValueError(
                'duplicate ids: {0}'.format([k for k, v in byid.most_common() if v > 1]))
        return cls(rows)
