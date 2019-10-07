import sys
import argparse
from pathlib import Path
import collections

import attr
from clldutils.clilib import ArgumentParserWithLogging, command, ParserError
from csvw.dsv import UnicodeWriter

from pygrambank.api import Grambank
from pygrambank.cldf import create
from pygrambank.sheet import Sheet, Row


@command()
def cldf(args):
    """
    grambank --repos=PATH/TO/Grambank --wiki_repos=PATH/TO/Grambank.wiki cldf PATH/TO/glottolog \
    PATH/TO/grambank-cldf

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
def check(args, write_report=True):
    """
    grambank --repos PATH/TO/Grambank check

    Run data quality checks on a grambank repository.
    """
    from csvw.dsv import UnicodeWriter

    report, counts = [], {}
    api = Grambank(args.repos)
    for sheet in api.iter_sheets():
        n = sheet.check(api, report=report)
        if (sheet.glottocode not in counts) or (n > counts[sheet.glottocode][0]):
            counts[sheet.glottocode] = (n, sheet.path.stem)

    selected = set(v[1] for v in counts.values())
    for row in report:
        row.insert(1, row[0] in selected)

    if report:
        if write_report:
            with UnicodeWriter('check.tsv', delimiter='\t') as w:
                w.writerow(['sheet', 'selected', 'level', 'feature', 'message'])
                w.writerows(report)
            print('Report written to check.tsv')
        raise ValueError('Repos check found WARNINGs or ERRORs')


@command()
def roundtrip(args):
    api = Grambank(args.repos)
    for sheet in api.iter_sheets():
        sheet.visit()


@command()
def fix(args):
    api = Grambank(args.repos)
    sheet = Sheet(api.sheets_dir / args.args[0])
    sheet.visit(row_visitor=eval(args.args[1]))


@command()
def new(args):
    """Create a new empty Grambank sheet.

    grambank new [PATH/TO/NEW/SHEET]
    """
    api = Grambank(args.repos, wiki=args.wiki_repos)
    name = args.args[0] if args.args else 'grambank_sheet.tsv'

    rows = collections.OrderedDict([
        ('Language_ID', lambda f: ''),
        ('Grambank_ID', lambda f: f.id),
        ('Possible Values', lambda f: f['Possible Values']),
        ('Value', lambda f: ''),
        ('Source', lambda f: ''),
        ('Comment', lambda f: ''),
        ('Contributed_datapoints', lambda f: ''),
        ('Clarifying comments', lambda f: f.wiki['Summary']),
        ('Relevant unit(s)', lambda f: f['Relevant unit(s)']),
        ('Function', lambda f: f['Function']),
        ('Form', lambda f: f['Form']),
    ])

    with UnicodeWriter(name, delimiter='\t') as w:
        w.writerow(rows.keys())
        for feature in api.features.values():
            w.writerow([v(feature) for v in rows.values()])


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
