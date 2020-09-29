"""
Clean mojibake from comments in sheets
"""
import pathlib

from ftfy import fix_encoding
from termcolor import colored

from pygrambank.sheet import Sheet


def visit(row):
    if row['Comment']:
        fixed = fix_encoding(row['Comment'])
        if fixed != row['Comment']:
            print('{}\n{}'.format(
                colored('---' + row['Comment'], 'red'),
                colored('+++' + fixed, 'green'),
            ))
            row['Comment'] = fixed
    return True


def run(args):
    for sheet in args.repos.iter_sheets():
        #p = pathlib.Path(sheet)
        read, written = sheet.visit(row_visitor=visit)
        #args.log.info('{0} rows read, {1} rows written'.format(read, written))
