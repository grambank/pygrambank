"""
Make sure a (set of) sheets contains rows for all active features.
"""
import collections

from csvw.dsv import UnicodeWriter
from clldutils.clilib import PathType

from pygrambank.sheet import Sheet
from pygrambank.cli_util import add_wiki_repos


def register(parser):
    parser.add_argument(
        'filename',
        metavar='SHEET',
        help="Path of a specific TSV file to check or substring of a filename (e.g. a glottocode)",
        default=None,
        type=PathType(type='file', must_exist=False),
    )
    add_wiki_repos(parser)


def run(args):
    if args.filename.exists():
        sheets = [Sheet(args.filename)]
    else:
        sheets = [s for s in args.repos.iter_sheets() if args.filename.name in s.path.name]
    for sheet in sheets:
        update(args, sheet)


def update(args, sheet):
    # Get rows as in "most updated sheet":
    rows = collections.OrderedDict([
        ('Feature_ID', lambda f: f.id),
        ('Feature', lambda f: f.wiki['title']),
        ('Possible Values', lambda f: f['Possible Values']),
        ('Clarifying comments', lambda f: f.wiki['Summary'].replace('\n', ' ')),
        ('Relevant unit(s)', lambda f: f['Relevant unit(s)']),
        ('Function', lambda f: f['Function']),
        ('Form', lambda f: f['Form']),
        ('Patron', lambda f: f.wiki['Patron']),
    ])
    active = {}
    for feature in args.repos.features.values():
        active[feature.id] = {k: v(feature) for k, v in rows.items()}

    # Read the current rows:
    fids, cols, rows = set(), None, []
    for i, r in enumerate(sheet.iterrows()):
        if i == 0:
            cols = list(r.keys())
        fids.add(r['Feature_ID'])
        rows.append(r)

    # Append missing features:
    added = set()
    for fid, crow in active.items():
        if fid not in fids:
            # Assemble the row, merging in matching cols from the most updated sheet.
            added.add(fid)
            rows.append(collections.OrderedDict([(col, crow.get(col, '')) for col in cols]))

    with UnicodeWriter(sheet.path, delimiter='\t', encoding='utf8') as w:
        for i, row in enumerate(rows):
            if i == 0:
                w.writerow(list(row.keys()))
            w.writerow(list(row.values()))
    if added:
        args.log.info('Sheet {}: added {} features'.format(sheet.path.name, len(added)))
