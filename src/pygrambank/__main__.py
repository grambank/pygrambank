import sys
import argparse
from pathlib import Path
import collections
import re

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
    """
    grambank --repos . fix SHEET_NAME "lambda r: r.update(Source=r['Source'].replace('), ', '); ')) or r"
    """
    api = Grambank(args.repos)
    sheet = Sheet(api.sheets_dir / args.args[0])
    sheet.visit(row_visitor=eval(args.args[1]))


@command()
def sourcecheck(args):
    pages = '(:\s*(?P<pages>([§IVXfpcilvx.0-9–,\-\s]*|(in\s+)?passim)))?'
    lower = "[A-ZÑa-zñçćäáàãåæéíïóöšßúü']"
    year = '([12][0-9]{3}([a-z])?((\-|/|,\s+)[0-9]{4})?|no date|forthcoming)'
    name = '((el|von|da|dos|van der|(V|v)an den|van de|van|de la|de)\s+)?[A-ZÑÅ]%(lower)s+(\-%(lower)s+)*' % locals()
    patterns = [
        re.compile('(?P<author>%(name)s(\s+(%(name)s|and|&))*(\s+et\s+al\.?)?)\s+(?P<year>%(year)s)\s*%(pages)s$' % locals()),
        re.compile('(?P<author>%(name)s(\s+(%(name)s|and|&))*(\s+et\s+al\.?)?)\s*\((?P<year>%(year)s)\s*%(pages)s\)$' % locals()),
    ]
    pc = re.compile('(p\.c\.?|personal communication|pers\.? comm\.)')

    #(2015): 117, 139
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
                    #print(ref)
    for k, v in sorted(missed.items())[1500:2500]:
        print(k, v)
    print(sum(missed.values()))


@command()
def new(args):
    """Create a new empty Grambank sheet.

    grambank new [PATH/TO/NEW/SHEET]
    """
    api = Grambank(args.repos, wiki=args.wiki_repos)
    name = args.args[0] if args.args else 'grambank_sheet.tsv'

    rows = collections.OrderedDict([
        ('Language_ID', lambda f: ''),
        ('Feature_ID', lambda f: f.id),
        ('Feature', lambda f: f.wiki['title']),
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
