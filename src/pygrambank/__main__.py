import sys
import argparse
from pathlib import Path
import collections
import re

from clldutils.clilib import ParserError, register_subcommands, get_parser_and_subparsers
from clldutils.loglib import Logging

from pygrambank.api import Grambank
from pygrambank.sheet import Sheet


def roundtrip(args):
    api = Grambank(args.repos)
    for sheet in api.iter_sheets():
        sheet.visit()


def fix(args):
    """
    grambank --repos . fix SHEET_NAME
    "lambda r: r.update(Source=r['Source'].replace('), ', '); ')) or r"
    """
    api = Grambank(args.repos)
    sheet = Sheet(api.sheets_dir / args.args[0])
    sheet.visit(row_visitor=eval(args.args[1]))


def sourcecheck(args):
    pages = '(:\s*(?P<pages>([§IVXfpcilvx.0-9–,\-\s]*|(in\s+)?passim)))?'
    lower = "[A-ZÑa-zñçćäáàãåæéíïóöšßúü']"
    year = '([12][0-9]{3}([a-z])?((\-|/|,\s+)[0-9]{4})?|no date|forthcoming)'
    name = '((el|von|da|dos|van der|(V|v)an den|van de|van|de la|de)\s+)?' \
           '[A-ZÑÅ]%(lower)s+(\-%(lower)s+)*' % locals()
    patterns = [
        re.compile(
            '(?P<author>%(name)s(\s+(%(name)s|and|&))*(\s+et\s+al\.?)?)'
            '\s+(?P<year>%(year)s)\s*%(pages)s$' % locals()),
        re.compile(
            '(?P<author>%(name)s(\s+(%(name)s|and|&))*(\s+et\s+al\.?)?)'
            '\s*\((?P<year>%(year)s)\s*%(pages)s\)$' % locals()),
    ]
    pc = re.compile('(p\.c\.?|personal communication|pers\.? comm\.)')

    # (2015): 117, 139
    early_parens = re.compile('\((?P<year>[0-9]{4})\):\s*(?P<pages>[0-9\s,\-]+)$')

    def replace_early_parens(m):
        return '({year}: {pages})'.format(**m.groupdict())

    missed = collections.Counter()
    api = Grambank(args.repos)

    def iter_refs(source):
        if source.startswith('(') and source.endswith(')') and '(' not in source[1:-1]:
            source = source[1:-1].strip()
        for ref in source.split(';'):
            ref = ref.strip()
            if re.search('[0-9]{4}((:[0-9\-]+)?\))?,\s+%s' % name, ref):
                # Something like Meier 2008, Mueller 2019
                for r in ref.split(','):
                    if r.strip() and not pc.search(r):
                        yield r.strip()
            else:
                if not pc.search(ref):
                    yield ref

    for sheet in api.iter_sheets():
        for row in sheet.iterrows():
            for ref in iter_refs(row['Source']):
                ref = early_parens.sub(replace_early_parens, ref)
                if ref.endswith(':'):
                    ref = ref[:-1].strip()
                for pattern in patterns:
                    if pattern.match(ref):
                        break
                else:
                    missed.update([ref])
    for k, v in sorted(missed.items())[1500:2500]:
        print(k, v)
    print(sum(missed.values()))


def refactor(args):
    """
    grambank refactor PATH/TO/GLOTTOLOG [old_style_sheet]+
    """
    from pygrambank.sheet import NewSheet
    from pyglottolog import Glottolog
    from pygrambank.util import write_tsv

    parser = argparse.ArgumentParser(prog='refactor')
    parser.add_argument('glottolog_repos', help="clone of glottolog/glottolog", type=Path)
    parser.add_argument('sheet', help="", type=Path)
    xargs = parser.parse_args(args.args)
    gl = Glottolog(xargs.glottolog_repos)
    gl = gl.languoids_by_code()

    api = Grambank(args.repos)
    contribs = {c.name: c for c in api.contributors}

    if xargs.sheet.is_dir():
        sheets = xargs.sheet.glob('*.xlsx')
    else:
        sheets = [xargs.sheet]

    for sheet in sheets:
        print(sheet, '...')
        sheet = NewSheet(sheet)
        try:
            gl_lang = gl[sheet.language_code]
        except KeyError:
            raise ValueError('Unknown language code: {0}'.format(sheet.language_code))
        n = '{0}_{1}.tsv'.format('-'.join(contribs[c].id for c in sheet.coders), gl_lang.id)
        write_tsv(sheet.fname, api.sheets_dir / n, gl_lang.id)
        print('...', api.sheets_dir / n)

    #
    # FIXME: should we also run checks now? I guess so.
    #


def propagate_gb20(args):
    """
    grambank --repos=PATH/TO/Grambank --wiki_repos=PATH/TO/Grambank.wiki  propagate_gb20

    Propagate changes in gb20.txt to all derived files (in Grambank repos and wiki).
    """
    api = Grambank(args.repos)
    api.gb20.listallwiki(args.wiki_repos)


def main(args=None, catch_all=False, parsed_args=None):
    import pygrambank.commands

    parser, subparsers = get_parser_and_subparsers('grambank')
    parser.add_argument(
        '--repos', help="clone of glottobank/Grambank", default=Path('.'), type=Path)
    register_subcommands(subparsers, pygrambank.commands)

    args = parsed_args or parser.parse_args(args=args)
    if not hasattr(args, "main"):
        parser.print_help()
        return 1

    args.repos = Grambank(args.repos, wiki=getattr(args, 'wiki_repos', None))
    with Logging(args.log, level=args.log_level):
        try:
            return args.main(args) or 0
        except KeyboardInterrupt:  # pragma: no cover
            return 0
        except ParserError as e:
            print(e)
            return main([args._command, '-h'])
        except Exception as e:
            if catch_all:  # pragma: no cover
                print(e)
                return 1
            raise


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
