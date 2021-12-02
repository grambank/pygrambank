"""
Write merged sheets for conflict resolution
"""
import pathlib
import itertools

from clldutils.clilib import PathType
from csvw.dsv import UnicodeWriter

from pygrambank.sheet import Row


def register(parser):
    parser.add_argument(
        '--outdir', default=pathlib.Path('.'), type=PathType(type='dir', must_exist=False))


def grouped_rows(sheets):
    for fid, vals in itertools.groupby(
        sorted(
            itertools.chain(*[[(r, s) for r in s.iterrows()] for s in sheets]),
            key=lambda i: (i[0]['Feature_ID'], i[1].path.name)),
        lambda r: r[0]['Feature_ID'],
    ):
        yield fid, [(r, s) for r, s in vals if r['Value']]


class Warnings:
    def __init__(self):
        # Accumulator for warning messages:
        self.messages = ''

    def __call__(self, msg, lineno, level=None, row_=None, **kw):
        # This will be called within Sheet.valid_row when problems are detected.
        self.messages += '\n{}:{}: {}'.format(level, row_['Feature_ID'], msg)


def run(args):
    api = args.repos
    if not args.outdir.exists():
        args.outdir.mkdir()

    # Iterate over groups of sheets for the same glottocode:
    for gc, sheets in itertools.groupby(
            sorted(api.iter_sheets(), key=lambda s: s.glottocode),
            lambda s: s.glottocode):
        if gc not in ['sina1266', 'meke1243']:
            continue
        sheets = list(sheets)
        if len(sheets) == 1:
            continue

        with UnicodeWriter(args.outdir / '{}.tsv'.format(gc), delimiter='\t') as w:
            w.writerow([
                'Feature_ID',
                'Value',
                'Conflict',
                'Classification of conflict',
                'Select',
                'Sheet',
                'Source',
                'Contributed_Datapoint',
                'Comment',
                'Warnings',
            ])
            # Iterate over rows grouped by feature ID:
            for fid, rows in grouped_rows(sheets):
                conflict = len(set(r[0]['Value'] for r in rows if r[0]['Value'])) > 1
                for row, sheet in rows:
                    # See what "grambank check" would do with the row:
                    warnings = Warnings()
                    sheet.valid_row(row, api, log=warnings)
                    w.writerow([
                        fid,
                        row['Value'],
                        str(conflict),
                        '',
                        '',
                        sheet.path.stem,
                        row.get('Source', ''),
                        ' '.join(Row.from_dict(row).contributed_datapoint),
                        row.get('Comment', ''),
                        warnings.messages,
                    ])
