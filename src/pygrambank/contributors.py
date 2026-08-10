import collections
import re
from dataclasses import dataclass, field, fields
from typing import List

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
    else:
        return None


def parse_roles(s):
    return [r.strip() for r in s.split(',') if r.strip()]


@dataclass
class Contributor:
    id: str
    last_name: str
    first_name: str
    contribution: List[str] = field(default_factory=lambda: parse_roles('Coder'))
    node: str = ''
    status: str = ''
    language_competence: str = ''
    github_username: str = ''
    email: str = ''
    photo: str = field(default='')
    bio: str = ''
    should_be_included_despite_no_coding: bool = False

    def __post_init__(self):
        self.contribution = parse_roles(self.contribution)
        invalid_roles = [role for role in self.contribution if role not in ROLES]
        if invalid_roles:
            raise ValueError('Invalid roles: {}'.format('; '.join(invalid_roles)))
        self.photo = parse_photo(self.photo)

    @property
    def name(self) -> str:
        return f'{self.first_name} {self.last_name}'

    @property
    def roles(self) -> List[str]:
        return sorted(self.contribution, key=lambda r: ROLES.index(r))


def norm_header(s):
    return s.lower().replace(' ', '_').replace('-', '_')


class Contributors(list):
    @classmethod
    def from_md(cls, fname):
        fields_ = {f.name for f in fields(Contributor)}
        header, rows = next(iter_markdown_tables(fname.read_text(encoding='utf8')))
        header = [norm_header(c) for c in header]
        rows = [
            Contributor(**{k: v for k, v in zip(header, row) if k in fields_})
            for row in rows]
        byid = collections.Counter(r.id for r in rows)
        if byid.most_common(1)[0][1] > 1:  # pragma: no cover
            msg = 'duplicate ids: {}'.format(
                [k for k, v in byid.most_common() if v > 1])
            raise ValueError(msg)
        return cls(rows)
