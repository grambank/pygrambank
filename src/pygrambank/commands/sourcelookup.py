"""
Lookup the references given in the `Source` column of a sheet in Glottolog hh.bib or the Grambank bib.
"""
import pathlib
import collections

from termcolor import colored
from cldfcatalog import Catalog

from pygrambank.sheet import Sheet
from pygrambank.cldf import BibliographyMatcher, GlottologGB
from pygrambank.bib import lgcodestr


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
    grambank = args.repos
    sheets = [Sheet(sh) for sh in args.sheets]

    # FIXME: code duplication with cldfbench
    print('Reading language data from Glottolog...')
    glottolog = GlottologGB(glottolog)
    languoids_by_ids = glottolog.languoids_by_ids
    descendants = glottolog.descendants_map

    print('Loading bibliography...')
    bibliography_entries = {}
    bibliography_entries.update(glottolog.bib('hh'))
    bibliography_entries.update(grambank.bib)

    bibkeys_by_glottocode = collections.defaultdict(set)
    for key, (typ, fields) in bibliography_entries.items():
        for lang_id in lgcodestr(fields.get('lgcode') or ''):
            if lang_id in languoids_by_ids:
                glottocode = languoids_by_ids[lang_id].id
                if glottocode in descendants:
                    for cl in descendants[glottocode]:
                        bibkeys_by_glottocode[cl].add(key)
                else:
                    print('---non-language', lang_id)

    for sheet in sheets:
        glottocode = sheet.glottocode

        print(colored(
            '\nSource look-up for sheet {}...\n'.format(sheet.path),
            attrs=['bold']))

        bib_matcher = BibliographyMatcher()
        for sheet_row in sheet.iter_row_objects(args.repos):
            bib_matcher.add_resolved_citation_to_row(
                sheet.glottocode,
                sheet_row,
                bibliography_entries,
                bibkeys_by_glottocode)

        print(colored('Resolved sources:', attrs=['bold']))
        for source, occurrence_count in bib_matcher.get_sources():
            print('{}\t{}\t{}'.format(occurrence_count, source.id, source))

        if bib_matcher.has_unresolved_citations():
            print()
            print(colored('Unresolved sources:', attrs=['bold']))
            for spec, occurrences in bib_matcher.get_unresolved_citations():
                if len(spec) == 3:
                    author, year, _ = spec
                    print('{}\t{} ({})'.format(occurrences, author, year))
                elif len(spec) == 2:
                    source_string, _ = spec
                    print('{}\t{}'.format(occurrences, source_string))
                else:  # pragma: nocover
                    # theoretically unreachable
                    print('{}\t{}'.format(occurrences, spec))
            if bibkeys_by_glottocode.get(glottocode):
                print()
                print(colored('Available sources:', attrs=['bold']))
                for bibkey in bibkeys_by_glottocode[glottocode]:
                    type_, fields = bibliography_entries[bibkey]
                    author = fields.get('author') or fields.get('editor') or '-'
                    year = fields.get('year') or '-'
                    print('{}\t{}\t{}'.format(
                        colored(bibkey, color='blue'),
                        type_,
                        colored('{} {}'.format(author, year), attrs=['bold'])))
            print()
            print(colored('FAIL', color='red'))
        else:
            print()
            print(colored('OK', color='green'))
