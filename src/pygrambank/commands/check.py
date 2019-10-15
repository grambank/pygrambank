"""
Check original_sheets/ for correctness.
"""
from csvw.dsv import UnicodeWriter


def register(parser):
    parser.add_argument(
        '--report',
        help="Path of TSV file, to which results will be written.",
        default=None,
    )


def run(args):
    report, counts = [], {}
    api = args.repos
    for sheet in api.iter_sheets():
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
