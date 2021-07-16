"""
Describe a (set of) sheets.

This includes checking for correctness - i.e. the functionality of `grambank check`.
While references will be parsed, the corresponding sources will **not** be looked up
in Glottolog (since this is slow). Thus, for a final check of a sheet, you must run
`grambank sourcelookup`.
"""
import collections

from termcolor import colored
from clldutils.clilib import PathType

from pygrambank.sheet import Sheet


def register(parser):
    parser.add_argument(
        'filename',
        metavar='SHEET',
        help="Path of a specific TSV file to check or substring of a filename (e.g. a glottocode)",
        default=None,
        type=PathType(type='file', must_exist=False),
    )
    parser.add_argument(
        '--columns',
        default=False,
        action='store_true',
        help='List columns of the sheet',
    )
    parser.add_argument(
        '--read-only',
        default=False,
        action='store_true',
        help='Do not roundtrip',
    )


def run(args):
    if args.filename.exists():
        sheets = [Sheet(args.filename)]
    else:
        sheets = [s for s in args.repos.iter_sheets() if args.filename.name in s.path.name]
    for sheet in sheets:
        describe(args, sheet)
        if not args.read_only:
            sheet.visit(lambda r: r)


def describe(args, sheet):
    rows = list(sheet.iter_row_objects(args.repos))

    def head(s):
        print()
        print(colored(s + ':', attrs=['bold']))

    head('Path')
    print(colored(str(sheet.path), 'green'))

    head('Check')
    sheet.check(args.repos)

    head('Dimensions')
    print('{} rows'.format(len(list(sheet.iterrows()))))
    for row in sheet.iterrows():
        print('{} columns'.format(len(row)))
        break

    head('Values')
    stats = collections.Counter(r.Value for r in rows)
    for k, v in stats.most_common():
        print('{}\t{}'.format(k, str(v).rjust(3)))
    print(colored('\t{}'.format(str(sum(stats.values())).rjust(3)), attrs=['bold']))

    refs = collections.Counter()
    for row in rows:
        for ref in row.sources:
            refs.update([ref.key])

    head('Sources')
    for (author, year, in_title), v in refs.most_common():
        print('{} {}{}:\t{}'.format(
            author,
            year,
            ' ({})'.format(in_title) if in_title else '',
            str(v).rjust(3)))

    head('Coders')
    coders = collections.Counter()
    for row in rows:
        coders.update(set(sheet.coders).union(row.contributed_datapoint))
    coders_by_id = {c.id: c.name for c in args.repos.contributors}

    for k, v in coders.most_common():
        if k in coders_by_id:
            print('{}\t{}:\t{}'.format(k, coders_by_id[k], str(v).rjust(3)))
        else:
            args.log.error('Unknown coder: "{}"'.format(k))  # pragma: no cover

    if args.columns:
        head('Columns')
        for row in sheet.iterrows():
            for col in row:
                print(col)
            break
