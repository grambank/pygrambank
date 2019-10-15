import re
from collections import OrderedDict
from itertools import groupby
import unicodedata

import attr
from csvw import dsv
from clldutils.path import as_unicode


GB_COLS = OrderedDict([
    ("Language_ID", ["iso-639-3", "Language", "Glottocode", "glottocode"]),
    ("Feature_ID", ["GramBank ID", "Grambank ID", "\* Feature number", "Grambank"]),
    ("Value", []),
    ("Source", []),
    ("Comment", ["Freetext comment"]),
    ("Feature Domain", ["Possible Values"]),
])

CODER_MAP = {
    'Damian Blasi': 'Damián E. Blasi',
    'Jemima Goodal': 'Jemima Goodall',
    'Nancy Poo': 'Nancy Bakker',
    'Hannah Haynie': 'Hannah J. Haynie',
    'Hans-Philipp Go¨bel': 'Hans-Philipp Göbel',
    'Cheryl Oluoch': 'Cheryl Akinyi Oluoch',
    'Alena Witzlack': 'Alena Witzlack-Makarevich',
    'Tania Martins': 'Tânia Martins',
}


@attr.s
class Row(object):
    Language_ID = attr.ib()
    Feature_ID = attr.ib()
    Value = attr.ib()
    Source = attr.ib()
    Comment = attr.ib()
    Feature_Domain = attr.ib()
    contributed_datapoints = attr.ib(default='')


@attr.s
class NewSheet(object):
    fname = attr.ib()

    @property
    def name(self):
        return unicodedata.normalize('NFC', unicode_from_path(self.fname.stem))

    @property
    def suffix(self):
        return self.fname.suffix

    @property
    def coders(self):
        return [
            CODER_MAP.get(n, n) or n for n in re.split(',\s+|\s+and\s+', self.name.split('_')[0])]

    @property
    def language(self):
        return self.name.split('_', 1)[1]

    @property
    def language_code(self):
        return self.language.split('[')[1].split(']')[0].strip()


def unicode_from_path(p):
    return as_unicode(p, 'windows-1252')


class Sheet(object):
    """
    Processing workflow:
    """
    name_pattern = re.compile(
        '(?P<coders>[A-Z]+(-[A-Z]+)*)_(?P<glottocode>[a-z0-9]{4}[0-9]{4})\.tsv$')

    def __init__(self, path):
        match = self.name_pattern.match(path.name)
        assert match, 'Invalid sheet name: {0}'.format(path.name)
        self.path = path
        self.coders = match.group('coders').split('-')
        self.glottocode = match.group('glottocode')

    def __str__(self):
        return str(self.path)

    def metadata(self, glottolog):
        languoid = glottolog.languoids_by_glottocode[self.glottocode]
        if languoid.level.name == 'dialect':
            for _, lgc, level in reversed(languoid.lineage):
                if level.name == 'language':
                    break
        else:
            lgc = languoid.id
        language = glottolog.languoids_by_glottocode[lgc]
        return dict(
            level=languoid.level.name,
            lineage=[l[1] for l in languoid.lineage],
            Language_ID=language.id,
            # Macroareas are assigned to language level nodes:
            Macroarea=language.macroareas[0].name,
            Latitude=languoid.latitude if languoid.latitude else language.latitude,
            Longitude=languoid.longitude if languoid.longitude else language.longitude,
            Family_name=languoid.lineage[0][0] if languoid.lineage else None,
            Family_id=languoid.lineage[0][1] if languoid.lineage else None,
        )

    def _reader(self, **kw):
        return dsv.reader(self.path, delimiter='\t', encoding='utf-8-sig', **kw)

    def iterrows(self):
        for row in self._reader(dicts=True):
            yield row

    def visit(self, row_visitor=None):
        if row_visitor is None:
            row_visitor = lambda r: r  # noqa: E731
        rows = list(self.iterrows())
        with dsv.UnicodeWriter(self.path, delimiter='\t', encoding='utf8') as w:
            for i, row in enumerate(rows):
                if i == 0:
                    w.writerow(list(row.keys()))
                res = row_visitor(row)
                if res:
                    w.writerow(list(row.values()))

    def check(self, api, report=None):
        def log(msg, row_=None, level='ERROR'):
            msg = [self.path.stem, level, row_['Feature_ID'] if row_ else '', msg]
            print('\t'.join(msg))
            if report is not None:
                report.append(msg)

        # Check the header:
        empty_index = []
        for i, row in enumerate(self._reader()):
            if i == 0:
                for col in ['Feature_ID', 'Value', 'Comment', 'Source']:
                    if col not in row:
                        log('missing column {0}'.format(col))
                for j, c in enumerate(row):
                    if not c:
                        empty_index.append(j)
                if len(set(row)) != len(row):
                    log('duplicate header')
            else:
                if not empty_index:
                    break
                for j in empty_index:
                    if row[j]:
                        log('non-empty cell with empty header: {0}'.format(row[j]), level='WARNING')

        res, nvalid, features = [], 0, set()
        for row in self.iterrows():
            if row['Feature_ID'] not in api.features:
                continue
            if row['Value']:
                if row['Value'] != '?' \
                        and row['Value'] not in api.features[row['Feature_ID']].domain:
                    log('invalid value {0}'.format(row['Value']), row_=row)
                else:
                    nvalid += 1

            if row['Value'] and not row['Source']:
                log('value without source', level='WARNING', row_=row)
            if row['Source'] and not row['Value']:
                log('source given, but no value', level='WARNING', row_=row)
            if row['Comment'] and not row['Value']:
                log('comment given, but no value', level='WARNING', row_=row)
            if row['Feature_ID'] in features:
                log('duplicate value for feature {0}'.format(
                    row['Feature_ID']), level='ERROR', row_=row)
            features.add(row['Feature_ID'])
            res.append(row)

        for gbid, rows in groupby(
            sorted(res, key=lambda r: r['Feature_ID']), lambda r: r['Feature_ID']
        ):
            rows = list(rows)
            if len(rows) > 1:
                # A feature is coded multiple times! If the codings are inconsistent, we raise
                # an error, otherwise the first value takes precedence.
                if len(set(r['Value'] for r in rows)) > 1:
                    log('inconsistent multiple codings: {0}'.format([r['Value'] for r in rows]))

        return nvalid

    def itervalues(self, api):
        for row in self.iterrows():
            row = self._value_row(row, api)
            if row:
                yield row

    def _value_row(self, row, api):
        for k in row:
            row[k] = row[k].strip() if row[k] else row[k]
        if not row['Value']:  # Drop rows with empty `Value` column.
            return None
        if row['Feature_ID'] not in api.features:  # Drop rows for obsolete features.
            return None

        # Uncertain values like "1?" are normalized as "?".
        if re.match('[0-9]\?$', row['Value']) or re.match('\?[0-9]$', row['Value']):
            row['Value'] = '?'
        return row
