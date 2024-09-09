"""
"""
from csvw.dsv import reader
from clldutils.clilib import PathType

from pygrambank.conflicts import check_conflicts


def register(parser):
    parser.add_argument('sheets', nargs='+', type=PathType(type='file'))


def run(args):
    for sheet in args.sheets:
        if len(args.sheets) > 1:
            args.log.info(f'\n## {sheet}')
        sheet_rows = list(reader(sheet, dicts=True, delimiter='\t'))
        conflict_count, errors = check_conflicts(sheet_rows)
        if errors:
            for err in errors:
                args.log.error(err)
            args.log.warning(f'There were errors in the {conflict_count} conflicts')
        else:
            args.log.info(f'{conflict_count} conflicts')
