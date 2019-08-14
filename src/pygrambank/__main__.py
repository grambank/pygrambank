from __future__ import unicode_literals
import sys
import argparse

from clldutils.clilib import ArgumentParserWithLogging, command, ParserError
from clldutils.path import Path

from pygrambank.api import Grambank
from pygrambank.cldf import create, preprocess


@command()
def check(args):
    """
    grambank --repos=PATH/TO/Grambank --wiki_repos=PATH/TO/Grambank.wiki check PATH/TO/glottolog

    creates a CLDF dataset from raw Grambank data sheets.
    """
    parser = argparse.ArgumentParser(prog='check', usage=__doc__)
    parser.add_argument('glottolog_repos', help="clone of glottolog/glottolog", type=Path)
    xargs = parser.parse_args(args.args)
    if not xargs.glottolog_repos.exists():
        raise ParserError('glottolog repos does not exist')
    if not args.wiki_repos.exists():
        raise ParserError('Grambank.wiki repos does not exist')
    preprocess(args.repos, xargs.glottolog_repos, args.wiki_repos)


@command()
def cldf(args):
    """
    grambank --repos=PATH/TO/Grambank --wiki_repos=PATH/TO/Grambank.wiki cldf PATH/TO/glottolog PATH/TO/grambank-cldf

    creates a CLDF dataset from raw Grambank data sheets.
    """
    parser = argparse.ArgumentParser(prog='cldf', usage=__doc__)
    parser.add_argument('glottolog_repos', help="clone of glottolog/glottolog", type=Path)
    parser.add_argument('cldf_repos', help="clone of glottobank/grambank-cldf", type=Path)
    xargs = parser.parse_args(args.args)
    if not xargs.glottolog_repos.exists():
        raise ParserError('glottolog repos does not exist')
    if not args.wiki_repos.exists():
        raise ParserError('Grambank.wiki repos does not exist')
    create(args.repos, xargs.glottolog_repos, args.wiki_repos, xargs.cldf_repos)


@command()
def roundtrip(args):
    from pygrambank.sheet import Sheet
    api = Grambank(args.repos)
    for p in api.sheets_dir.iterdir():
        if p.is_file() and p.name != '.gitattributes':
            sheet = Sheet(p)
            sheet.visit()


@command()
def refactor(args):
    """
    grambank refactor PATH/TO/GLOTTOLOG [old_style_sheet]+
    """
    from pygrambank.sheet import NewSheet
    from pyglottolog import Glottolog
    from pygrambank.util import write_tsv

    parser = argparse.ArgumentParser(prog='refactor')
    parser.add_argument('glottolog_repos', help="clone of glottolog/glottolog", type=Path)
    xargs = parser.parse_args(args.args)
    gl = Glottolog(xargs.glottolog_repos)

    api = Grambank(args.repos)
    contribs = {c.name: c for c in api.contributors}

    for p in args.args[1:]:
        sheet = NewSheet(Path(p))
        gl_lang = gl.languoid(sheet.language_code)
        n = '{0}_{1}.tsv'.format('-'.join(contribs[c].id for c in sheet.coders), gl_lang.id)
        write_tsv(sheet.fname, api.sheets_dir / n, gl_lang.id)

    #
    # FIXME: should we also run checks now? I guess so.
    #


@command()
def propagate_gb20(args):
    """
    grambank --repos=PATH/TO/Grambank --wiki_repos=PATH/TO/Grambank.wiki  propagate_gb20

    Propagate changes in gb20.txt to all derived files (in Grambank repos and wiki).
    """
    api = Grambank(args.repos)
    api.gb20.listallwiki(args.wiki_repos)
    api.gb20.features_sheet()
    api.gb20.grambank_sheet()


def main():  # pragma: no cover
    parser = ArgumentParserWithLogging('pygrambank')
    parser.add_argument('--repos', help="clone of glottobank/Grambank", type=Path)
    parser.add_argument('--wiki_repos', help="clone of glottobank/Grambank.wiki", type=Path)
    sys.exit(parser.main())


if __name__ == "__main__":  # pragma: no cover
    main()
