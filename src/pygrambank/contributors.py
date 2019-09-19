import collections

import attr


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
        header = None
        rows = []
        for line in fname.open():
            line = line.strip()
            if line.startswith('|') and line.endswith('|'):
                row = [c.strip() for c in line[1:-1].split('|')]
                if header is None:
                    header = [norm_header(s) for s in row]
                    continue
                elif set(line) == set('|:-'):
                    continue
                rows.append(Contributor(**dict(zip(header, row))))
        byid = collections.Counter([r.id for r in rows])
        if byid.most_common(1)[0][1] > 1:
            raise ValueError(
                'duplicate ids: {0}'.format([k for k, v in byid.most_common() if v > 1]))
        return cls(rows)
