"""
Create a new, empty sheet
"""
from pathlib import Path

from csvw.dsv import UnicodeWriter

from pygrambank.cli_util import add_wiki_repos

FNAME = 'For_coders/Grambank_most_updated_sheet.tsv'


def register(parser):
    parser.add_argument(
        '--out',
        help='Path for output sheet',
        default=FNAME)
    add_wiki_repos(parser)


def normalised_summary(feature):
    summary = feature.wiki.get('Summary') or ''
    summary = summary.replace('\n', ' ')
    summary = summary.replace('\t', ' ')
    return summary


def assemble_row(row_spec, feature):
    try:
        return [format_func(feature) for format_func in row_spec.values()]
    except Exception as err:
        # add some more information to the error, so I can find the faulty wiki
        # page.
        raise ValueError(f'{feature.id}: {err}') from err


def run(args):
    name = args.repos.path(args.out) if args.out == FNAME else Path(args.out)

    features = {
        f.id: f
        for f in args.repos.features.values()
        if f.get('Binary_Multistate') != 'multi'}

    row_spec = {
        'Feature_ID': lambda f: f.id,
        'Feature': lambda f: f.wiki_or_gb20('title', 'Feature'),
        'Possible Values': lambda f: f['Possible Values'],
        'Language_ID': lambda _: '',
        'Value': lambda _: '',
        'Source': lambda _: '',
        'Comment': lambda _: '',
        'Contributed_Datapoints': lambda _: '',
        'Clarifying comments': normalised_summary,
        'Relevant unit(s)': lambda f: f['Relevant unit(s)'],
        'Patron': lambda f: f.wiki_or_gb20('Patron', 'Feature Patron'),
    }

    with UnicodeWriter(name, delimiter='\t') as w:
        w.writerow(row_spec)
        w.writerows(assemble_row(row_spec, f) for f in features.values())
