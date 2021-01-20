"""
Clean mojibake from comments in sheets
"""
from ftfy import fix_encoding
from termcolor import colored


def visit(row):  # pragma: no cover
    if row['Comment']:
        fixed = fix_encoding(row['Comment'])
        if fixed != row['Comment']:
            print('{}\n{}'.format(
                colored('---' + row['Comment'], 'red'),
                colored('+++' + fixed, 'green'),
            ))
            row['Comment'] = fixed
    return True


def run(args):  # pragma: no cover
    for sheet in args.repos.iter_sheets():
        sheet.visit(row_visitor=visit)
