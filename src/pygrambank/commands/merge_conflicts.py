"""

"""
import collections
from datetime import datetime
import itertools
import subprocess

from csvw.dsv import reader, UnicodeWriter
from clldutils.clilib import PathType
from clldutils.misc import nfilter

from .check_conflicts import check
from pygrambank.sheet import Sheet

# flake8: noqa

CODERS = {
    'Farah07': 'FE',
    'Hedvig': 'HS',
    'Hoju': 'HC',
    'Jill': 'JSA',
    'lschlabbach': 'LS',
    'Michael': 'MM',
    'Michael90EVAMPI': 'MM',
    'SydneyRey': 'SR',
    'tobiaskweber': 'TWE',
    'vickygruner': 'VG',
    'Victoria': 'VG',
}


def register(parser):
    parser.add_argument('sheets', type=PathType(type='file'), nargs='+')
    parser.add_argument('-f', '--force', action='store_true')


def get_coder(p):
    log = subprocess.check_output(
        ['git', 'log', '--format=format:%an', '--', str(p)]).decode('utf8')
    for line in log.splitlines():
        first_name = line.strip().split()[0]
        if first_name in CODERS:
            return CODERS[first_name]


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


def git_modification_time(path):
    """Return last modification date of `path` as a unix timestamp.

    Uses git log to determine the time.
    """
    most_recent_log_entry = subprocess.check_output(
        ['git', 'log', '-n1', '--format=format:%at|%ct', '--', path]).decode('utf-8')
    if most_recent_log_entry:
        author_time, committer_time = most_recent_log_entry.split('|')
        return int(author_time or committer_time)
    else:
        raise ValueError(
            '{}: cannot determine last-modified date '
            '-- git log does not know what this file is, apparently...'.format(
                path))


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
    sheets = args.sheets or sorted(
        args.repos.path('conflicts').glob('*.tsv'),
        key=lambda p: p.name)

    for sheet in sheets:
        print('\n#', sheet.stem)
        ok, nc = check(sheet)
        if not ok or not nc:
            print(
                'Skipping {}:'.format(sheet.stem),
                '`grambank check_conflicts` found errors.')
            continue

        try:
            rows, sources = rows_and_sourcesheets(sheet, active)
        except ValueError as e:
            print('Skipping {}: Failed to merge rows: {}'.format(sheet.stem, e))
            continue
        coder = get_coder(sheet)
        if sheet.stem == 'sout2989':
            coder = 'JE-HS'
        if not coder:
            print(
                'Skipping {}:'.format(sheet.stem),
                "Couldn't determine coder")
            continue

        merged_sheet_name = args.repos.path(
            'original_sheets', '{}_{}.tsv'.format(coder, sheet.stem))
        source_sheets = [
            args.repos.path('original_sheets', src.split('.')[0] + '.tsv')
            for src in sources
            if src.split('_')[0] != coder]

        if not args.force:
            try:
                conflict_mod_time = git_modification_time(sheet)
                sheet_mod_times = map(git_modification_time, source_sheets)
                newer_sheets = [
                    (sheet_path, mod_time)
                    for sheet_path, mod_time in zip(source_sheets, sheet_mod_times)
                    if mod_time > conflict_mod_time]
                if newer_sheets:
                    print(
                        'Skipping {}:'.format(sheet.stem),
                        'Data sheet changed more recently than the conflict sheet!')
                    print(' * {}: {}'.format(sheet, datetime.fromtimestamp(conflict_mod_time)))
                    for sheet_path, mod_time in newer_sheets:
                        print(' * {}: {}'.format(sheet_path, datetime.fromtimestamp(mod_time)))
                    continue
            except ValueError as e:
                print(e)
                continue

        print('{{{}}} -> {}'.format(
            '; '.join(str(p) for p in sorted(source_sheets)),
            merged_sheet_name))
        write(merged_sheet_name, rows, args.repos.features)
        for p in source_sheets:
            if p.exists():
                p.unlink()
            else:
                print('{}: file not found'.format(p))

        print('checks for {}:'.format(merged_sheet_name))
        merged_sheet = Sheet(merged_sheet_name)
        merged_sheet.check(args.repos)

        archive_dest = args.repos.path('conflicts_resolved', sheet.name)
        if archive_dest.exists():
            # just append the conflict sheet to the previous resolved conflict;
            # very hacky:
            # XXX: this assumes that we don't change the column layout
            # XXX: also: introducing multi-line colnames would break this
            print('cat', sheet, '>>', archive_dest)
            with open(sheet, encoding='utf-8') as fin:
                # drop header
                _ = next(fin)
                with open(archive_dest, 'a') as fout:
                    fout.write(''.join(fin))
            sheet.unlink()
        else:
            print(sheet, '->', archive_dest)
            sheet.rename(archive_dest)
