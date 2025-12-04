"""
Fix sheet(s) by applying a python lambda function to all its rows.
"""
import pathlib

from pygrambank.sheet import Sheet


def register(parser):
    parser.add_argument(
        'lambda_',
        metavar='lambda',
        help='Python lambda accepting row-dict as sole argument, '
             'e.g. "lambda r: r.update(Source=r[\'Source\'].replace(\'\'), \'\', \'\'); \'\')) or r"')
    parser.add_argument(
        'sheets',
        metavar='SHEETS',
        nargs='+',
    )


def run(args):
    for sheet in args.sheets:
        p = pathlib.Path(sheet)
        if p.exists() and p.is_file():
            sheet = p.name
        sheet = Sheet(args.repos.sheets_dir / sheet)
        args.log.info(f'fixing {sheet.path}')
        read, written = sheet.visit(row_visitor=eval(args.lambda_))
        args.log.info(f'{read} rows read, {written} rows written')
