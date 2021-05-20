"""
Recode a file, i.e. change its encoding to UTF-8.
"""
from clldutils.clilib import PathType


def register(parser):
    parser.add_argument('path', nargs='+', type=PathType(type='file'))
    parser.add_argument(
        '--encoding',
        default='cp1252',
        choices=['cp1252', 'macroman', 'mixed'],
    )


def run(args):
    for p in args.path:
        if args.encoding == 'mixed':
            # Dunno how this happens, but sometimes, different lines are
            # encoded differently ...
            c = []
            for line in p.read_bytes().split(b'\n'):
                l = []
                for chunk in line.split(b'\t'):
                    try:
                        l.append(chunk.decode('utf8'))
                    except:
                        try:
                            l.append(chunk.decode('cp1252'))
                        except:
                            print(chunk)
                            raise
                c.append('\t'.join(l))
            c = '\n'.join(c)
        else:
            c = p.read_text(encoding=args.encoding)
        p.write_text(c, encoding='utf8')
