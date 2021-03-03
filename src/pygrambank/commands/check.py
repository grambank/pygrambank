"""
Check original_sheets/ for correctness.
"""
from csvw.dsv import UnicodeWriter
from clldutils.clilib import PathType

from pygrambank.sheet import Sheet
from pygrambank.util import iterunique


def register(parser):
    parser.add_argument(
        '--filename',
        help="Path of a specific TSV file to check",
        default=None,
        type=PathType(type='file'),
    )
    parser.add_argument(
        '--report',
        help="Path of TSV file, to which results will be written.",
        default=None,
    )
    parser.add_argument(
        '--verbose',
        default=False,
        action='store_true',
    )


def run(args):
    report, counts = [], {}
    api = args.repos

    if args.filename:
        sheets = [Sheet(args.filename)]
    else:
        sheets = [(s, list(s.itervalues(api))) for s in api.iter_sheets()]
        sheets = (s[0] for s in iterunique(sheets, verbose=args.verbose))

    for sheet in sorted(sheets, key=lambda s: s.path):
        n = sheet.check(api, report=report)
        if (sheet.glottocode not in counts) or (n > counts[sheet.glottocode][0]):
            counts[sheet.glottocode] = (n, sheet.path.stem)

    selected = set(v[1] for v in counts.values())
    for row in report:
        row.insert(1, row[0] in selected)

    if report and args.report:
        with UnicodeWriter(args.report, delimiter='\t') as w:
            w.writerow(['sheet', 'selected', 'level', 'feature', 'message'])
            w.writerows(report)
        args.log.info('Report written to {0}'.format(args.report))
    args.log.error('Repos check found WARNINGs or ERRORs')
