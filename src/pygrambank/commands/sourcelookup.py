"""
Lookup the references given in the `Source` column of a sheet in Glottolog hh.bib or the Grambank bib.
"""
import pathlib
import collections

from termcolor import colored
from cldfcatalog import Catalog

from pygrambank.sheet import Sheet
from pygrambank.cldf import refs, GlottologGB, Bibs, languoid_id_map


def register(parser):
    parser.add_argument(
        'glottolog',
        metavar='GLOTTOLOG',
        help="clone of glottolog/glottolog",
        type=pathlib.Path,
    )
    parser.add_argument(
        'sheets',
        type=pathlib.Path,
        nargs='+',
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
    sheets = [Sheet(sh) for sh in args.sheets]

    print('Reading languoid ids from Glottolog...')
    glottolog = GlottologGB(glottolog)
    id_to_glottocode = languoid_id_map(glottolog, [s.glottocode for s in sheets])

    print('Loading bibliography...')
    bibs = Bibs(glottolog, args.repos)

    keys_by_glottocode = collections.defaultdict(set)
    for key, code in bibs.iter_codes():
        if code in id_to_glottocode:
            keys_by_glottocode[id_to_glottocode[code]].add(key)

    for sheet in sheets:
        print(colored(
            '\nSource look-up for sheet {}...\n'.format(sheet.path),
            attrs=['bold']))
        sources, unresolved, lgks = refs(
            args.repos, sheet.glottocode, bibs, keys_by_glottocode, sheet)

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
