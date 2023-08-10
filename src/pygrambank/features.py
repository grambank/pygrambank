import re
from collections import OrderedDict, Counter

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

    def wiki_or_gb20(self, wiki_key, gb20_key):
        return self.wiki.get(wiki_key) or self.get(gb20_key) or ''

    @classmethod
    def from_chunk(cls, chunk, wiki):
        items = [
            re.fullmatch(r'([^:]*?)\s*:\s*(.*)', line).groups()
            for line in chunk.split('\n')
            if ':' in line and not line.startswith('#')]
        # Make sure there are no duplicate keys:
        keys = Counter(i[0] for i in items)
        if len(keys) != len(items):
            raise ValueError('Duplicate keys: {}'.format(
                ';'.join(key for key, count in keys.items() if count > 1)))
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
        else:  # pragma: no cover
            return self.wiki_or_gb20('Summary', 'Clarifying comments')

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
            re.split(
                r'\s+(?:&|and)\s+',
                self.wiki_or_gb20('Patron', 'Feature Patron').strip())]


class GB20(object):
    CHUNK_SEP = '\n\n\n\n'

    def __init__(self, path):
        self.path = path

    def _iterfeatures(self, wiki):
        for chunk in self.path.read_text(encoding='utf-8').split(self.CHUNK_SEP):
            if chunk.strip():
                yield Feature.from_chunk(chunk, wiki)

    def read_features(self, wiki):
        features = {
            f['Grambank ID']: f
            for f in self._iterfeatures(wiki)}
        # binarised features inherit info from non-binarised parents.
        for feature in features.values():
            parent_id = feature.get('Multistate_parent')
            if not parent_id or parent_id not in features:
                continue
            parent_wiki = features[parent_id].wiki
            for key in ['Patron', 'Summary']:
                if not feature.wiki.get(key) and parent_wiki.get(key):
                    feature.wiki[key] = parent_wiki[key]
        return features

    def save(self, features):
        with self.path.open('w', encoding='utf8') as fp:
            fp.write('# -*- coding: utf-8 -*-\n')
            fp.write(self.CHUNK_SEP.join(f.as_chunk() for f in features))
