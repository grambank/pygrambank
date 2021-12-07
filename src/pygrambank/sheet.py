import re
import itertools
import collections

import attr
from csvw import dsv

from pygrambank.srctok import iter_ayps


@attr.s
class Source:
    author = attr.ib()
    year = attr.ib()
    pages = attr.ib()
    in_title = attr.ib()

    @property
    def key(self):
        return self.author, self.year, self.in_title


@attr.s
class Row:
    Feature_ID = attr.ib()
    Value = attr.ib()
    Source = attr.ib()
    Comment = attr.ib(default=None)
    contributed_datapoint = attr.ib(
        default=attr.Factory(list),
        converter=lambda s: re.findall('[A-Z]+(?=[^A-Z]|$)', s) if s else [])
    Source_comment = attr.ib(default=None)

    @classmethod
    def from_dict(cls, d):
        fields = list(attr.fields_dict(cls).keys())
        kw = {}
        for k, v in d.items():
            if ('ontributed' in k) and ('atapoint' in k):
                k = 'contributed_datapoint'
            if k in fields:
                kw[k] = v
        return cls(**kw)

    @property
    def sources(self):
        return [Source(*ayp) for ayp in iter_ayps(self.Source)]


class Sheet(object):
    """
    Processing workflow:
    """
    name_pattern = re.compile(
        r'(?P<coders>[A-Z]+(-[A-Z]+)*)_(?P<glottocode>[a-z0-9]{4}[0-9]{4})\.tsv$')

    def __init__(self, path):
        match = self.name_pattern.match(path.name)
        assert match, 'Invalid sheet name: {0}'.format(path.name)
        self.path = path
        self.coders = match.group('coders').replace('CB-PE-AS', 'HunterGatherer').split('-')
        self.glottocode = match.group('glottocode')
        self._rows = None

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
        if not language.macroareas:
            print('--- no macroareas: {}'.format(self.glottocode))
        return dict(
            level=languoid.level.name,
            lineage=[lang[1] for lang in languoid.lineage],
            Language_level_ID=language.id,
            # Macroareas are assigned to language level nodes:
            Macroarea=language.macroareas[0].name if language.macroareas else '',
            Latitude=languoid.latitude if languoid.latitude else language.latitude,
            Longitude=languoid.longitude if languoid.longitude else language.longitude,
            Family_name=languoid.lineage[0][0] if languoid.lineage else None,
            Family_level_ID=languoid.lineage[0][1] if languoid.lineage else None,
        )

    def _reader(self, **kw):
        return dsv.reader(self.path, delimiter='\t', encoding='utf-8-sig', **kw)

    def iterrows(self):
        if self._rows is None:
            self._rows = []
            for row in self._reader(dicts=True):
                self._rows.append(row)
                yield row
        else:
            for row in self._rows:
                yield row

    def visit(self, row_visitor=None):
        """
        Apply `row_visitor` to all rows in a sheet.

        :param row_visitor:
        :return: Pair of `int`s specifying the number of rows read and written.
        """
        if row_visitor is None:
            row_visitor = lambda r: r  # noqa: E731
        rows = list(self.iterrows())
        count = 0
        with dsv.UnicodeWriter(self.path, delimiter='\t', encoding='utf8') as w:
            for i, row in enumerate(rows):
                if i == 0:
                    w.writerow(list(row.keys()))
                res = row_visitor(row)
                if res:
                    w.writerow(list(row.values()))
                    count += 1
        # Make sure calling iterrows again will re-read from disk:
        self._rows = None
        return (len(rows), count)

    def valid_row(self, row, api, lineno=None, log=None, features=None):
        fid = row.get('Feature_ID')
        if not fid:
            return False
        res = True
        if not re.match('GB[0-9]{3}|(GBDRS.+)|TE[0-9]+|TS[0-9]+$', fid):
            if row.get('Value'):
                if log:
                    log('invalid Feature_ID: {0}'.format(fid),
                        lineno=lineno,
                        level='ERROR',
                        row_=row)
            res = False
        if fid not in api.features:
            return False
        if row.get('Value'):
            if row['Value'] != '?' and row['Value'] not in api.features[row['Feature_ID']].domain:
                if log:
                    log('invalid value: {0}'.format(row['Value']), lineno=lineno, row_=row)
                res = False
        else:
            res = False

        if row['Value'] and not row['Source']:
            if log:
                log('value without source', lineno=lineno, level='WARNING', row_=row)
            res = False
        if row['Source'] and not row['Value']:
            if log:
                log('source given, but no value', lineno=lineno, level='WARNING', row_=row)
            res = False
        if row['Comment']:
            if re.search('check', row['Comment'].lower()):
                if log:  # pragma: no cover
                    log('comment contains string "check"', lineno=lineno, level='WARNING', row_=row)
            if not row['Value']:
                if log:
                    log('comment given, but no value', lineno=lineno, level='WARNING', row_=row)
                res = False
        if row['Feature_ID'] in (features or set()):
            if log:
                log('duplicate value for feature {0}'.format(
                    row['Feature_ID']), lineno=lineno, level='ERROR', row_=row)
            res = False
        return res

    def check(self, api, report=None):
        def log(msg, row_=None, level='ERROR', lineno=-1):
            msg = [
                self.path.stem,
                level,
                "{}".format(lineno if lineno != -1 else '?'),
                row_['Feature_ID'] if row_ else '',
                msg]
            print('\t'.join(msg))
            if report is not None:
                report.append(msg)

        # Check the header:
        empty_index = []
        for line, row in enumerate(self._reader()):
            if line == 0:
                for col in ['Feature_ID', 'Value', 'Comment', 'Source']:
                    if col not in row:
                        log('missing column {0}'.format(col), lineno=line)
                for j, c in enumerate(row):
                    if not c:
                        empty_index.append(j)
                if len(set(row)) != len(row):
                    dupes = collections.Counter([h for h in row if row.count(h) > 1])
                    log('duplicate header column(s) %r' % dupes, lineno=line)
            else:
                if not empty_index:
                    break
                for j in empty_index:
                    if row[j]:
                        log('non-empty cell with empty header: {0}'.format(row[j]),
                            lineno=line,
                            level='WARNING')

        res, nvalid, features = [], 0, set()
        for line, row in enumerate(self.iterrows(), 2):  # +2 to get line number correct
            if self.valid_row(row, api, lineno=line, log=log, features=features):
                nvalid += 1
            features.add(row['Feature_ID'])
            res.append(row)

        try:
            for gbid, rows in itertools.groupby(
                sorted(res, key=lambda r: r['Feature_ID']), lambda r: r['Feature_ID']
            ):
                rows = list(rows)
                if len(rows) > 1:
                    # A feature is coded multiple times! If the codings are inconsistent, we raise
                    # an error, otherwise the first value takes precedence.
                    if len(set(r['Value'] for r in rows)) > 1:
                        log('inconsistent multiple codings: {0}'.format([r['Value'] for r in rows]))
        except:  # pragma: no cover  # noqa
            for row in res:
                if not row['Feature_ID']:
                    print(row)
                    break
            print(self.path)
            raise
        return nvalid

    def itervalues(self, api):
        try:
            for row in self.iterrows():
                if self.valid_row(row, api):
                    yield row
        except:  # pragma: no cover # noqa: E722
            print(self.path)
            raise

    def iter_row_objects(self, api):
        for row in self.itervalues(api):
            yield Row.from_dict(row)
