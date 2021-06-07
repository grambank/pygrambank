"""
Create a new, empty sheet
"""
import pathlib
import collections

from csvw.dsv import UnicodeWriter

from pygrambank.cli_util import add_wiki_repos

FNAME = 'For_coders/Grambank_most_updated_sheet.tsv'


def register(parser):
    parser.add_argument(
        '--out',
        help='Path for output sheet',
        default=FNAME)
    add_wiki_repos(parser)


def run(args):
    if args.out == FNAME:  # pragma: no cover
        name = args.repos.path(args.out)
    else:
        name = pathlib.Path(args.out)

    rows = collections.OrderedDict([
        ('Feature_ID', lambda f: f.id),
        ('Feature', lambda f: f.wiki['title']),
        ('Possible Values', lambda f: f['Possible Values']),
        ('Value', lambda f: ''),
        ('Source', lambda f: ''),
        ('Comment', lambda f: ''),
        ('Contributed_Datapoints', lambda f: ''),
        ('Clarifying comments', lambda f: f.wiki['Summary'].replace('\n', ' ')),
        ('Relevant unit(s)', lambda f: f['Relevant unit(s)']),
        ('Function', lambda f: f['Function']),
        ('Form', lambda f: f['Form']),
        ('Patron', lambda f: f.wiki['Patron']),
    ])

    with UnicodeWriter(name, delimiter='\t') as w:
        w.writerow(rows.keys())
        for feature in args.repos.features.values():
            w.writerow([v(feature) for v in rows.values()])
