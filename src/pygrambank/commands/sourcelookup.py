"""

"""
import pathlib
import collections

from termcolor import colored

from pygrambank.sheet import Sheet
from pygrambank.cldf import refs


def register(parser):
    parser.add_argument(
        'sheet',
        type=pathlib.Path,
    )
    parser.add_argument(
        'glottolog',
        metavar='GLOTTOLOG',
        help="clone of glottolog/glottolog",
        type=pathlib.Path,
    )


def run(args):
    sources, unresolved, lgks = refs(args.repos, args.glottolog, Sheet(args.sheet))
    seen = collections.defaultdict(list)
    print(colored('Resolved sources:', attrs=['bold']))
    for src in sources:
        seen[src.id].append(src)
    for srcid, srcs in seen.items():
        print('{}\t{}\t{}'.format(len(srcs), srcid, srcs[0]))
    if unresolved:
        print()
        print(colored('Unresolved sources:', attrs=['bold']))
        for (author, year, code), v in unresolved.most_common():
            print('{}\t{} {}'.format(v, author, year))
        if lgks:
            print()
            print(colored('Available sources:', attrs=['bold']))
            for (k, t, a, y) in lgks:
                print('{}\t{}\t{}'.format(
                    colored(k, color='blue'),
                    t,
                    colored('{} {}'.format(a, y), attrs=['bold'])))
    print()
    print(colored('FAIL' if unresolved else 'OK', color='red' if unresolved else 'green'))