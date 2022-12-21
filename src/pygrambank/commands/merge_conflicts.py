"""

"""
import itertools
import subprocess
import collections

from csvw.dsv import reader, UnicodeWriter
from clldutils.misc import nfilter

from .check_conflicts import check
from pygrambank.sheet import Sheet

# flake8: noqa

CODERS = collections.OrderedDict([
    ('SydneyRey', 'SR'),
    ('Michael90EVAMPI', 'MM'),
    ('Michael', 'MM'),
    ('Jill', 'JSA'),
    ('vickygruner', 'VG'),
    ('Hedvig', 'HS'),
])


def get_coder(p):
    log = subprocess.check_output(['git', 'log', str(p)]).decode('utf8')
    committers = []
    for line in log.split('\n'):
        if line.startswith('Author:'):
            committers.append(line.replace('Author:', '').strip().split()[0])
    for name, initials in CODERS.items():
        if name in committers:
            return initials


def merged_rows(rows, active):
    if all(r['Conflict'].lower().startswith('true') for r in rows):
        for row in rows:
            if row['Select'].lower().strip() == 'true':
                return row
        assert rows[0]['Feature_ID'] not in active, str(rows)
        return None
    elif all(r['Conflict'].lower().strip() == 'false' for r in rows):
        row = rows[0]
        for k in ['Sheet', 'Comment', 'Source']:
            row[k] = [row[k]]
        for r in rows[1:]:
            for k in ['Sheet', 'Comment', 'Source']:
                row[k].append(r[k])
        for k, sep in [('Sheet', ' '), ('Comment', '. '), ('Source', '; ')]:
            row[k] = sep.join(nfilter(row[k]))
        return row
    raise ValueError(rows)


def rows_and_sourcesheets(sheet, active):
    allrows, sourcesheets = [], []

    def clean_row(row):
        sourcesheets.extend(row['Sheet'].split())
        coders = '-'.join(s.split('_')[0] for s in row['Sheet'].split())
        coders = coders.split('-')
        del row['Sheet']
        if row.get('Contributed_Datapoint'):
            row['Contributed_Datapoint'] += ' ' + ' '.join(coders)
        else:
            row['Contributed_Datapoint'] = ' '.join(coders)
        allrows.append(row)

    #fids = collections.Counter([r['Feature_ID'] for r in reader(sheet, dicts=True, delimiter='\t')])
    #print(len(fids), sum(fids.values()))

    for fid, rows in itertools.groupby(
        sorted(reader(sheet, dicts=True, delimiter='\t'), key=lambda r: r['Feature_ID']),
        lambda r: r['Feature_ID'],
    ):
        rows = list(rows)
        if len(rows) == 1:
            clean_row(rows[0])
        else:
            row = merged_rows(rows, active)
            if row:
                clean_row(row)
    return allrows, set(sourcesheets)


def write(p, rows, features):
    rows = collections.OrderedDict([(r['Feature_ID'], r) for r in rows])
    cols = 'Feature_ID Value Source Contributed_Datapoint Comment'.split()
    with UnicodeWriter(p, delimiter='\t') as writer:
        writer.writerow(cols)

        for feature in features.values():
            row = rows.pop(feature.id, None)
            if not row:
                row = {k: '' for k in cols}
                row['Feature_ID'] = feature.id
            writer.writerow([row.get(col, '') for col in cols])
        for row in rows.values():
            writer.writerow([row.get(col, '') for col in cols])


def run(args):
    active = list(args.repos.features)

    for sheet in sorted(args.repos.path('conflicts').glob('*.tsv'), key=lambda p: p.name):
        #if sheet.stem != 'brah1256':
        #    continue
        ok, nc = check(sheet)
        if not ok or not nc:
            continue

        print(sheet.stem)
        try:
            rows, sources = rows_and_sourcesheets(sheet, active)
        except ValueError as e:
            print('Failed to merge rows:', e)
            continue
        coder = get_coder(sheet)
        if sheet.stem == 'sout2989':
            coder = 'JE-HS'
        assert coder, str(sheet)

        merged_sheet_name = args.repos.path(
            'original_sheets', '{}_{}.tsv'.format(coder, sheet.stem))
        print('writing', merged_sheet_name)
        write(merged_sheet_name, rows, args.repos.features)

        for src in sources:
            if src.split('_')[0] != coder:
                p = args.repos.path('original_sheets', src.split('.')[0] + '.tsv')
                if p.exists():
                    print('removing', p)
                    p.unlink()
                else:
                    print("ERROR: won't remove", p, '-- file not found')

        print('checks for', merged_sheet_name)
        merged_sheet = Sheet(merged_sheet_name)
        merged_sheet.check(args.repos)

        archive_dest = args.repos.path('conflicts_resolved', sheet.name)
        if archive_dest.exists():
            print(
                "ERROR: won't move", sheet, 'to', archive_dest,
                '-- destination already exists.')
        else:
            print(sheet, '->', archive_dest)
            sheet.rename(archive_dest)
