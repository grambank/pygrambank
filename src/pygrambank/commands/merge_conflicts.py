"""

"""
import itertools
import subprocess

from csvw.dsv import reader, UnicodeWriter

from .check_conflicts import check


CODERS = {
    'SydneyRey': 'SR',
    'Michael90EVAMPI': 'MM',
    'Michael': 'MM',
    'Jill': 'JSA',
    'Hedvig': 'HS',
}


def get_coder(p):
    log = subprocess.check_output(['git', 'log', str(p)]).decode('utf8')
    for line in log.split('\n'):
        if line.startswith('Author:'):
            name = line.replace('Author:', '').strip().split()[0]
            if name in CODERS:
                return CODERS[name]


def iter_rows(sheet):
    def clean_row(row):
        coders = row['Sheet'].split('_')[0]
        coders = coders.split('-')
        del row['Sheet']
        if row.get('Contributed_Datapoint'):
            row['Contributed_Datapoint'] += ' ' + ' '.join(coders)
        else:
            row['Contributed_Datapoint'] = ' '.join(coders)
        return row

    for fid, rows in itertools.groupby(
        sorted(reader(sheet, dicts=True, delimiter='\t'), key=lambda r: r['Feature_ID']),
        lambda r: r['Feature_ID'],
    ):
        rows = list(rows)
        if len(rows) == 1:
            yield clean_row(rows[0])
        else:
            for row in rows:
                if row['Select'] == 'True':
                    yield clean_row(row)
                    break


def write(p, rows):
    cols = 'Feature_ID Value Source Contributed_Datapoint Comment'.split()
    with UnicodeWriter(p, delimiter='\t') as writer:
        writer.writerow(cols)
        for row in rows:
            writer.writerow([row.get(col, '') for col in cols])


def run(args):
    for sheet in sorted(args.repos.path('conflicts').glob('*.tsv'), key=lambda p: p.name):
        ok, nc = check(sheet)
        if ok and nc:
            coder = get_coder(sheet)
            assert coder, str(sheet)
            write(
                args.repos.path('original_sheets', '{}_{}.tsv'.format(coder, sheet.stem)),
                list(iter_rows(sheet)))
