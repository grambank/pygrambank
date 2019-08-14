# coding: utf-8
from __future__ import unicode_literals, print_function
import re
from collections import defaultdict, OrderedDict
from itertools import groupby
import unicodedata

import attr
from csvw import dsv
from clldutils.misc import lazyproperty, nfilter
from clldutils.path import Path, as_unicode


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
        return self.language.split('[')[1].split(']')[0].strip()


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
    name_pattern = re.compile(
        '(?P<coders>[A-Z]+(-[A-Z]+)*)_(?P<glottocode>[a-z0-9]{4}[0-9]{4})\.tsv$')

    def __init__(self, path):
        match = self.name_pattern.match(path.name)
        assert match, 'Invalid sheet name: {0}'.format(path.name)
        self.path = path
        self.coders = match.group('coders').split('-')
        self.glottocode = match.group('glottocode')

    def iterrows(self):
        for row in dsv.reader(self.path, delimiter='\t', encoding='utf-8-sig', dicts=True):
            yield row

    def visit(self, row_visitor=None):
        if row_visitor is None:
            row_visitor = lambda r: r
        rows = list(self.iterrows())
        with dsv.UnicodeWriter(self.path, delimiter='\t', encoding='utf8') as w:
            for i, row in enumerate(rows):
                if i == 0:
                    w.writerow(list(row.keys()))
                row = row_visitor(row)
                if row:
                    w.writerow(list(row.values()))

    def check(self, api, report=None):
        def log(msg, row_=None, level='ERROR'):
            msg = [self.path.stem, level, row_['Feature_ID'] if row_ else '', msg]
            print('\t'.join(msg))
            if report is not None:
                report.append(msg)

        res, nvalid = [], 0
        for row in self.iterrows():
            if row['Feature_ID'] not in api.features:
                continue
            if row['Value'] and row['Value'] != '?' and row['Value'] not in api.features[row['Feature_ID']].domain:
                log('invalid value {0}'.format(row['Value']), row_=row)
            else:
                nvalid += 1
            #
            # FIXME: check source! and if source, then value!
            #
            if row['Value'] and not row['Source']:
                log('value without source', level='WARNING', row_=row)
            if row['Source'] and not row['Value']:
                log('source given, but no value', level='WARNING', row_=row)
            if row['Comment'] and not row['Value']:
                log('comment given, but no value', level='WARNING', row_=row)
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
