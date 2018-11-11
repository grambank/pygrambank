from __future__ import unicode_literals
import sys
import argparse

from clldutils.clilib import ArgumentParserWithLogging, command, ParserError
from clldutils.path import Path

from pygrambank.cldf import create


@command()
def cldf(args):
    usage = """
    grambank %(prog)s - creates a CLDF dataset from raw Grambank data sheets.
    """
    parser = argparse.ArgumentParser(prog='cldf', usage=usage)
    parser.add_argument('repos', help="clone of glottobank/Grambank", type=Path)
    parser.add_argument('glottolog_repos', help="clone of clld/glottolog", type=Path)
    parser.add_argument('wiki_repos', help="clone of glottobank/Grambank.wiki", type=Path)
    parser.add_argument('cldf_repos', help="clone of glottobank/grambank-cldf", type=Path)
    xargs = parser.parse_args(args.args)
    if not xargs.glottolog_repos.exists():
        raise ParserError('glottolog repos does not exist')
    if not xargs.wiki_repos.exists():
        raise ParserError('Grambank.wiki repos does not exist')
    create(xargs.repos, xargs.glottolog_repos, xargs.wiki_repos, xargs.cldf_repos)


def main():  # pragma: no cover
    parser = ArgumentParserWithLogging('pygrambank')
    sys.exit(parser.main())


if __name__ == "__main__":  # pragma: no cover
    main()
