"""
Recode a file, i.e. change its encoding to UTF-8.
"""
from clldutils.clilib import PathType


def register(parser):
    parser.add_argument('path', nargs='+', type=PathType(type='file'))
    parser.add_argument(
        '--encoding',
        default='cp1252',
        choices=['cp1252', 'macroman'],
    )


def run(args):
    for p in args.path:
        c = p.read_text(encoding=args.encoding)
        p.write_text(c, encoding='utf8')
