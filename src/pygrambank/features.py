import re
from collections import OrderedDict

from clldutils.misc import lazyproperty


patrons = {
    'Alena': 'AWM',
    'Alena Witzlack-Makarevich': 'AWM',
    'Hannah': 'HJH',
    'Hannah J. Haynie': 'HJH',
    'Harald': 'HH',
    'Harald Hammarström': 'HH',
    'Hedvig': 'HS',
    'Hedvig Skirgård': 'HS',
    'Jakob': 'JLE',
    'Jakob Lesage': 'JLE',
    'Jeremy': 'JC',
    'Jeremy Collins': 'JC',
    'Jay': 'JLA',
    'Jay Latarche': 'JLA',
}


class Feature(OrderedDict):
    def __init__(self, spec, wiki):
        OrderedDict.__init__(self, spec)
        self._wiki = wiki
        self.domain = OrderedDict()
        spec = self['Possible Values'].replace('multistate', '').strip()
        delimiter = ',' if ',' in spec else ';'
        for val in spec.split(delimiter):
            val, desc = re.split(r'\s*:\s*', val.strip())
            int(val)
            self.domain[val] = desc

    @classmethod
    def from_chunk(cls, chunk, wiki):
        items = []
        for line in chunk.split('\n'):
            if ':' in line and not line.startswith('#'):
                items.append(re.split(r'\s*:\s*', line.strip(), 1))
        # Make sure there are no duplicate keys:
        assert len(set(i[0] for i in items)) == len(items)
        res = cls(items, wiki)
        for k, v in res.wiki.items():
            if k in res:
                if res[k] != v:  # pragma: no cover
                    print('++++', k, res[k], v)
        return res

    def as_chunk(self):
        return ''.join('{0}: {1}\n'.format(k, v) for k, v in self.items())

    @lazyproperty
    def wiki(self):
        res = OrderedDict()
        p = self._wiki / '{}.md'.format(self.id)
        if not p.exists():
            return res
        title, header, lines = None, None, []
        for line in p.read_text(encoding='utf-8-sig').split('\n'):
            line = line.strip()
            if (not title) and line.startswith('#'):
                res['title'] = title = line.replace('#', '').strip()
            elif line.startswith('## '):
                if lines:
                    res[header] = '\n'.join(lines).strip()
                    lines = []
                header = line.replace('## ', '').strip()
            else:
                lines.append(line)
        if lines:
            res[header] = '\n'.join(lines).strip()
        res['Patron'] = res['Patron'].split('\n')[0]
        return res

    @lazyproperty
    def description(self):
        if self._wiki.joinpath('{0}.md'.format(self.id)).exists():
            return self._wiki.joinpath('{0}.md'.format(self.id)).read_text(encoding='utf-8-sig')
        return self['Clarifying Comments']  # pragma: no cover

    @lazyproperty
    def id(self):
        return self['Grambank ID']

    @lazyproperty
    def name(self):
        return self['Feature']

    @lazyproperty
    def patrons(self):
        return [
            patrons[k] for k in
            re.split(r'\s+(?:&|and)\s+', self.wiki['Patron'].strip())]


class GB20(object):
    CHUNK_SEP = '\n\n\n\n'

    def __init__(self, path):
        self.path = path

    def iterfeatures(self, wiki):
        for chunk in self.path.read_text(encoding='utf-8').split(self.CHUNK_SEP):
            if chunk.strip():
                yield Feature.from_chunk(chunk, wiki)

    def save(self, features):
        with self.path.open('w', encoding='utf8') as fp:
            fp.write('# -*- coding: utf-8 -*-\n')
            fp.write(self.CHUNK_SEP.join(f.as_chunk() for f in features))

    def listallwiki(self, wiki):
        fn = wiki / "List-of-all-features.md"
        currentlist = []
        for m in re.finditer(
            r"\*\s*(?P<gbid>(GB)?\d\d\d)\s+\[(?P<feature>[^]]+)]\((?P<link>[^)]+)\)",
            fn.read_text(encoding='utf-8')
        ):
            res = m.groupdict()
            if not res['gbid'].startswith('GB'):
                res['gbid'] = 'GB' + res['gbid']
            currentlist.append(res)

        active = set(f.id for f in self.iterfeatures(wiki))

        print(len(active), "active")
        print(len(currentlist) - len(active), "inactive")

        with fn.open('w', encoding='utf8') as fp:
            fp.write("Active in the GramBank feature set:\n\n")
            for spec in currentlist:
                if spec['gbid'] in active:
                    fp.write("* %(gbid)s [%(feature)s](%(link)s)\n" % spec)

            fp.write(
                "\n\nNo longer active in the GramBank feature set (for historical interest only):"
                "\n\n")
            for spec in currentlist:
                if spec['gbid'] not in active:
                    fp.write("* %(gbid)s [%(feature)s](%(link)s)\n" % spec)
