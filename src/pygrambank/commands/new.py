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


def normalised_summary(feature_dict, feature):
    summary = parent_wiki_get(feature_dict, feature, 'Summary') or ''
    summary = summary.replace('\n', ' ')
    summary = summary.replace('\t', ' ')
    return summary


def parent_wiki_get(feature_dict, feature, key):
    parent = feature.get('Multistate_parent')
    if parent and parent in feature_dict:
        return feature_dict[parent].wiki.get(key) or feature.wiki.get(key)
    else:
        return feature.wiki.get(key)


def assemble_row(row_spec, feature):
    try:
        return [format_func(feature) for format_func in row_spec.values()]
    except Exception as e:
        # add some more information to the error, so I can find the faulty wiki
        # page.
        raise ValueError('{}: {}'.format(feature.id, e))


def run(args):
    if args.out == FNAME:  # pragma: no cover
        name = args.repos.path(args.out)
    else:
        name = pathlib.Path(args.out)

    features = collections.OrderedDict(
        (f.id, f)
        for f in args.repos.features.values())

    row_spec = collections.OrderedDict([
        ('Feature_ID', lambda f: f.id),
        ('Feature', lambda f: f.wiki_or_gb20('title', 'Feature')),
        ('Possible Values', lambda f: f['Possible Values']),
        ('Language_ID', lambda f: ''),
        ('Value', lambda f: ''),
        ('Source', lambda f: ''),
        ('Comment', lambda f: ''),
        ('Contributed_Datapoints', lambda f: ''),
        ('Clarifying comments', lambda f: normalised_summary(features, f)),
        ('Relevant unit(s)', lambda f: f['Relevant unit(s)']),
        ('Patron', lambda f: parent_wiki_get(features, f, 'Patron')),
    ])

    with UnicodeWriter(name, delimiter='\t') as w:
        w.writerow(row_spec)
        w.writerows(assemble_row(row_spec, f) for f in features.values())
