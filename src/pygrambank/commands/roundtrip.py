"""

"""
from csvw.dsv import UnicodeWriter, reader
from clldutils.clilib import PathType


def register(parser):
    parser.add_argument('sheet', type=PathType(type='file'))


def run(args):
    rows = list(reader(args.sheet, delimiter='\t'))
    with UnicodeWriter(args.sheet, delimiter='\t') as w:
        w.writerows(rows)
