"""
Write merged sheets for conflict resolution
"""
import pathlib
import itertools

from clldutils.clilib import PathType
from csvw.dsv import UnicodeWriter

"""
2 only keep the following columns: "Source", "Value" "Contributed_Datapints", "Feature_ID" and "Comment"
3 add resp. filename as column
4 merge in columns from the output of pygrambank check
5 pull apart filename into coder and glottocode
6 do some basic checks for duplicates of Feature_ID + glottocode and check for conflicts
7 for any glottocode where there is at least one conflict, output glottocode-specific sheet 
(with name of selected sheet for that glottocode but containing all coding for that glottocode) 
with cols for "Conflict" and "Check warning" into a separate file in the repos from original_sheet. 
Add empty cols for "Classification of conflict" and "Select" for coder workflow
8 together with a small set of GB coders, go through a few of these sheets using a standardised 
set of possibly classification of conflicts (and solve check warnings along the way when relevant)
9 evaluate classification schema with coders
10 go through rest of sheets with at least one conflict
"""

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
        yield fid, list(vals)


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
                'Comment',
                'Warnings',
            ])
            # Iterate over rows grouped by feature ID:
            for fid, rows in grouped_rows(sheets):
                conflict = len(set(r[0]['Value'] for r in rows)) > 1
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
                        row.get('Comment', ''),
                        warnings.messages,
                    ])
