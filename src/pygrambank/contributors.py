import collections

import attr
from clldutils.markup import iter_markdown_tables


@attr.s
class Contributor(object):
    id = attr.ib()
    last_name = attr.ib()
    first_name = attr.ib()
    contribution = attr.ib()

    @property
    def name(self):
        return '{0.first_name} {0.last_name}'.format(self)


def norm_header(s):
    return s.lower().replace(' ', '_')


class Contributors(list):
    @classmethod
    def from_md(cls, fname):
        header, rows = next(iter_markdown_tables(fname.read_text(encoding='utf8')))
        rows = [Contributor(**dict(zip([norm_header(c) for c in header], row))) for row in rows]
        byid = collections.Counter([r.id for r in rows])
        if byid.most_common(1)[0][1] > 1:  # pragma: no cover
            raise ValueError(
                'duplicate ids: {0}'.format([k for k, v in byid.most_common() if v > 1]))
        return cls(rows)
