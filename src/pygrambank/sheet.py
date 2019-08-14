# coding: utf-8
from __future__ import unicode_literals, print_function
import re
from collections import defaultdict, OrderedDict
from itertools import groupby
import unicodedata

import attr
import xlrd
import openpyxl
from csvw import dsv
from clldutils.misc import lazyproperty, nfilter
from clldutils.path import Path, as_unicode

LANGUAGE_TO_GLOTTOCODE = {
    "Guwidj [ung]": "guwi1238",
    "Munumburru [ung]": "munu1238",
    "Ngarnawu [ung]": "ngar1285",
    "Waladjangari (Wurla) [ung]": "wurl1240",
    "Woljamidi [ung]": "woly1239",
    "Yagaria-Hua [ygr]": "huaa1250",
    "Yagaria-Move [ygr]": "move1241",
    "Hokkien [nan]": "hokk1242",
    "Chaozhou [nan]": "chao1238",
    "Kinikinao [gqn]": "huaa1250",
    "Terena [ter]": "move1241",
}

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
        return [CODER_MAP.get(n, n) or n for n in re.split(',\s+|\s+and\s+', self.name.split('_')[0])]

    @property
    def language(self):
        return self.name.split('_', 1)[1]

    @property
    def language_code(self):
        if '[' in self.language:
            return self.language.split('[')[1].split(']')[0].strip()
        return self.language


def unicode_from_path(p):
    return as_unicode(p, 'windows-1252')


def normalized_feature_id(s):
    if s.isdigit():
        s = "GB" + str(s).zfill(3)
    elif s.startswith("GB") and len(s) != 5:
        s = "GB" + str(s[2:]).zfill(3)
    return s


def normalize_comment(s):
    """
    Normalize comments, turning things like "????" into "?".

    :param s: The original comment
    :return: The normalized comment as string
    """
    if s:
        if set(s) == {'#'}:
            return
        if set(s) == {'?'}:
            return '?'
        return s


def normalized_value(sheet, v, feature):
    if not v:
        return
    if v in {
        '?',
        '??',
        'n/a',
        'N/A',
        'n.a.',
        'n.a',
        'N.A.',
        'N.A',
        '-',
        'NODATA',
        '? - Not known'
        '*',
        "*",
        '\\',
        'x',
    }:
        return '?'
    # Uncertain values like "1?" are normalized as "?".
    if re.match('[0-9]\?$', v) or re.match('\?[0-9]$', v):
        return '?'
    if v not in feature.domain:
        print('ERROR: {0}: invalid value "{1}" for feature {2}'.format(
            sheet.path.name, v, feature.id))
        return '?'
    return v


class Sheet(object):
    """
    Processing workflow:
    """
    valid_suffixes = ['.xlsx', '.xls', '.csv']

    def __init__(self, path, glottolog, features):
        path = Path(path)

        # We support reading the sheet from the preparsed TSV file:
        self._from_tsv = path.suffix == '.tsv'

        m = re.match(
            '(?P<coder>[^_]+)_(?P<lgname>[^\[]+)\[(?P<lgid>[^\]]+)\]\s*(\.xlsb)?$', path.stem)
        if not m or ((not self._from_tsv) and path.suffix not in self.valid_suffixes):
            # We can't read metadata from the filename, or the format is not supported.
            raise ValueError(path)  # pragma: no cover

        self.path = path
        if self._from_tsv:
            for suffix in self.valid_suffixes:
                origin = path.parent.joinpath(unicode_from_path(path.stem) + suffix)
                if origin.exists():
                    self.path = origin
                    break

        self.coder = unicode_from_path(m.group('coder').strip())
        self.lgname = unicode_from_path(m.group('lgname').strip())
        self.lgid = m.group('lgid').strip()
        self.lgnamecode = '{0.lgname} [{0.lgid}]'.format(self)
        languoid = glottolog.languoids_by_ids[self.lgid]
        lgc = languoid.id
        self.level = languoid.level.name
        self.lineage = [l[1] for l in languoid.lineage]
        if languoid.level.name == 'dialect':
            for _, lgc, level in reversed(languoid.lineage):
                if level.name == 'language':
                    break
            else:
                lgc = languoid.id
        language = glottolog.languoids_by_glottocode[lgc]
        self.language_id = language.id

        # Macroareas are assigned to language level nodes:
        self.macroarea = language.macroareas[0].name,
        self.latitude = languoid.latitude if languoid.latitude else language.latitude
        self.longitude = languoid.longitude if languoid.longitude else language.longitude

        self.family_name = languoid.lineage[0][0] if languoid.lineage else None
        self.family_id = languoid.lineage[0][1] if languoid.lineage else None
        self.glottocode = LANGUAGE_TO_GLOTTOCODE.get(self.lgnamecode, languoid.id)
        self._features = features

    @lazyproperty
    def rows(self):
        if self._from_tsv:
            res = []
            for row in dsv.reader(
                self.path.parent / (unicode_from_path(self.path.stem) + '.tsv'),
                delimiter='\t',
                encoding='utf-8-sig',
                dicts=True
            ):
                if self.path.suffix == '.tsv':
                    # This TSV was *not* created from an original sheet, so needs to be normalized
                    # now!
                    row = self._normalized_row(row)
                    if row is None:
                        continue
                res.append(row)

            dedupres = []
            for gbid, rows in groupby(
                sorted(res, key=lambda r: r['Feature_ID']), lambda r: r['Feature_ID']
            ):
                rows = list(rows)
                if len(rows) > 1:
                    # A feature is coded multiple times! If the codings are inconsistent, we raise
                    # an error, otherwise the first value takes precedence.
                    if len(set(r['Value'] for r in rows)) > 1:
                        print(
                            'ERROR:{0}:{1} inconsistent multiple codings: {2}'.format(
                                self.path.name, gbid, [r['Value'] for r in rows]))
                    else:
                        dedupres.append(rows[0])
                else:
                    dedupres.append(rows[0])
            return dedupres
        _rows = {
            '.xlsx': self._xlsx_to_rows,
            '.xls': self._xls_to_rows,
            '.csv': self._csv_to_rows}[self.path.suffix]()
        return nfilter(self._normalized_row(OrderedDict(zip(_rows[0], row))) for row in _rows[1:])

    def write_tsv(self, restrict_cols=False, fn=None):
        try:
            fn = fn or self.path.parent / (unicode_from_path(self.path.stem) + '.tsv')
        except UnicodeDecodeError:
            print([fn, self.path.parent, self.path.stem])
            fn = fn or self.path.parent / (self.path.stem + '.tsv')
        with dsv.UnicodeWriter(fn, delimiter='\t') as w:
            for i, row in enumerate(self.rows):
                if i == 0:
                    w.writerow(list(GB_COLS.keys()) if restrict_cols else list(row.keys()))
                w.writerow(
                    [row.get(col, '') for col in GB_COLS.keys()]
                    if restrict_cols else list(row.values()))
                yield row

    def _normalized_row(self, row):
        for k in row:
            row[k] = row[k].strip() if row[k] else row[k]
        if 'Value' not in row or (not row['Value']):
            # Drop rows with no `Value` column or empty `Value` column.
            return None

        # Normalize column names:
        if 'Grambank ID' in row and 'Feature_ID' in row:
            row['Feature'] = row.pop('Feature_ID')

        for col, aliases in GB_COLS.items():
            if col not in row:
                for k in list(row.keys()):
                    if k in aliases:
                        row[col] = row.pop(k)
                        break
                else:
                    row[col] = ''

        # Normalize colum values:
        row['Feature_ID'] = normalized_feature_id(row['Feature_ID'])
        if row['Feature_ID'] not in self._features:  # Drop rows for obsolete features.
            return None
        row['Language_ID'] = self.glottocode
        row['Value'] = normalized_value(self, row['Value'], self._features[row['Feature_ID']])
        row['Comment'] = normalize_comment(row['Comment'])
        return row

    #
    # Helper methods to read various tabular file formats.
    #
    @staticmethod
    def _read_excel_value(x):
        if x is None:
            return ""
        if type(x) == type(0.0):
            return '{0}'.format(int(x))
        return '{0}'.format(x).strip()

    def _xlsx_to_rows(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            sheet = openpyxl.load_workbook(str(self.path), data_only=True).active
        rows = []
        empty_rows = 0
        skip_cols = set()
        for i, row in enumerate(sheet.rows):
            if i == 0:
                for j, c in enumerate(row):
                    # There's a couple of sheets with > 10,000 columns, labeled with "Column<no>".
                    # We cut these out to reduce TSV bloat.
                    if re.match('Column[0-9]+$', '{0}'.format(c.value)):
                        skip_cols.add(j)
            row = [self._read_excel_value(c.value) for j, c in enumerate(row) if j not in skip_cols]
            if set(row) == {''}:  # pragma: no cover
                empty_rows += 1
                if empty_rows > 1000:
                    # There's a couple of sheets with > 100,000 (mostly empty) rows.
                    # After encountering more than 1,000, we stop reading.
                    break
                else:
                    continue
            rows.append(row)
        return rows

    def _xls_to_rows(self):
        wb = xlrd.open_workbook(str(self.path))
        rows_by_sheetname = defaultdict(list)
        for sheet in wb.sheets():  # We read all sheets in the workbook.
            for row in range(sheet.nrows):
                rows_by_sheetname[sheet.name].append(
                    [self._read_excel_value(sheet.cell_value(row, col))
                     for col in range(sheet.ncols)])
        # Now select the proper sheet:
        if len(rows_by_sheetname) > 1:
            for sheetname in ["GramBank", '"Empty" GramBank Sheet']:
                if sheetname in rows_by_sheetname:
                    return rows_by_sheetname[sheetname]
        return list(rows_by_sheetname.values())[0]

    def _csv_to_rows(self):
        def read(encoding):
            with self.path.open(encoding=encoding) as csvfile:
                line = csvfile.readline()
                delimiter = ','
                if ';' in line and ((',' not in line) or (line.index(';') < line.index(','))):
                    delimiter = ';'
            spamreader = dsv.reader(
                self.path, delimiter=delimiter, quotechar='"', doublequote=True, encoding=encoding)
            return [row for row in spamreader]

        try:
            return read('utf-8-sig')
        except UnicodeDecodeError:  # pragma: no cover
            return read('cp1252')
