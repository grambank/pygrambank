"""
Lookup the references given in the `Source` column of a sheet in Glottolog or the Grambank bib.
"""
import pathlib
import collections

from termcolor import colored
from cldfcatalog import Catalog

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
    parser.add_argument(
        '--glottolog-version',
        default=None,
        help="tag to checkout glottolog/glottolog to",
    )


def run(args):
    if args.glottolog_version:  # pragma: no cover
        with Catalog(args.glottolog, args.glottolog_version) as glottolog:
            run_(args, glottolog.dir)
    else:  # pragma: no cover
        run_(args, args.glottolog)


def run_(args, glottolog):  # pragma: no cover
    sources, unresolved, lgks = refs(args.repos, glottolog, Sheet(args.sheet))
    seen = collections.defaultdict(list)
    print(colored('Resolved sources:', attrs=['bold']))
    for src in sources:
        seen[src.id].append(src)
    for srcid, srcs in seen.items():
        print('{}\t{}\t{}'.format(len(srcs), srcid, srcs[0]))
    if unresolved:
        print()
        print(colored('Unresolved sources:', attrs=['bold']))
        for spec, v in unresolved.most_common():
            try:
                author, year, code = spec
                print('{}\t{} {}'.format(v, author, year))
            except ValueError:
                print(spec)
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
