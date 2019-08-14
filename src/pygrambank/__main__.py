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
def refactor(args):
    import itertools
    import collections
    from pygrambank.sheet import Sheet, NewSheet
    from pyglottolog import Glottolog
    from pygrambank.util import write_tsv
    from shutil import copy
    from tqdm import tqdm

    parser = argparse.ArgumentParser(prog='refactor')
    parser.add_argument('glottolog_repos', help="clone of glottolog/glottolog", type=Path)
    xargs = parser.parse_args(args.args)
    gl = Glottolog(xargs.glottolog_repos)
    langs_by_id = {l.id: l for l in gl.languoids()}
    langs_by_code = gl.languoids_by_code(nodes=langs_by_id)
    for v in langs_by_id.values():
        if v.name not in langs_by_code:
            langs_by_code[v.name] = v

    api = Grambank(args.repos)
    sheets = {k: [NewSheet(f) for f in v] for k, v in itertools.groupby(
        sorted(api.sheets_dir.iterdir(), key=lambda p: p.stem),
        lambda p: p.stem) if '_' in k}
    #for s in sorted(sheets):
    #    print(s)

    contribs = {c.name: c for c in api.contributors}

    bycoder = collections.defaultdict(list)
    for s, files in sheets.items():
        if len(files) > 2:
            print(s, files)
        for coder in files[0].coders:
            bycoder[coder].append(s)

        assert files[0].language_code in langs_by_code

    for c in bycoder:
        assert c in contribs

    for s, files in tqdm(sorted(sheets.items(), key=lambda i: i[0]), total=len(sheets)):
    #for s, files in sorted(sheets.items(), key=lambda i: i[0]):
        sheet = files[0]
        n = '{0}_{1}.tsv'.format('-'.join(contribs[c].id for c in sheet.coders), langs_by_code[sheet.language_code].id)

        original = None
        if len(files) == 1:
            original = files[0].fname
        else:
            assert len(files) == 2
            for f in files:
                if f.suffix != '.tsv':
                    original = f.fname
                    break
        assert original
        try:
            write_tsv(original, api.sheets_dir / n, langs_by_code[sheet.language_code].id)
        except:
            print(original)
            raise

        for f in files:
            if f.fname == original:
                copy(str(original), str(api.repos / 'obsolete_sheets' / original.name))
            f.fname.unlink()


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
