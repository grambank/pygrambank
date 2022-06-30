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


def check_feature_dependencies(rows, log):
    values = {
        r.Feature_ID: r
        for r in rows
        if r.Feature_ID and r.Value}

    def _value(feat):
        row = values.get(feat)
        return row.Value if row else None

    def _comment(feat):   # pragma: nocover
        row = values.get(feat)
        return row.Comment if row else None

    if (_value('GB408')
        == _value('GB409')
        == _value('GB410')
        == '0'
    ):
        log.error(colored(
            "GB408, GB409, and GB410 can't all be 0",
            color='red'))  # pragma: nocover

    if (_value('GB131')
        == _value('GB132')
        == _value('GB133')
        == '0'
    ):
        log.error(colored(
            "GB131, GB132, and GB133 can't all be 0",
            color='red'))  # pragma: nocover

    if (_value('GB083')
        == _value('GB084')
        == _value('GB121')
        == _value('GB521')
        == _value('GB309')
        == '0'
    ):
        log.error(colored(
            "GB309 can't be 0 if GB083, GB084, GB121 and GB521 are all 0",
            color='red'))  # pragma: nocover

    if (_value('GB333')
        == _value('GB334')
        == _value('GB335')
        == _value('GB336')
        == '0'
    ):
        for feat in ('GB333', 'GB334', 'GB335', 'GB336'):  # pragma: nocover
            if not _comment(feat):
                log.error(colored(
                    '{} must have a comment'
                    ' if GB333, GB334, GB335, and GB336 are all 0'.format(feat),
                    color='red'))

    for feat in (
        'GB026', 'GB303', 'GB320', 'GB166', 'GB197', 'GB129', 'GB285', 'GB336',
        'GB260', 'GB165', 'GB319'
    ):
        if _value(feat) == '1' and not _comment(feat):
            log.error(colored(
                '{} should not be coded 1 without a comment'.format(feat),
                color='red'))


def describe(args, sheet):
    rows = list(sheet.iter_row_objects(args.repos))

    def head(s):
        print()
        print(colored(s + ':', attrs=['bold']))

    head('Path')
    print(str(sheet.path))

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

    check_feature_dependencies(rows, args.log)

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
            args.log.error(colored('Unknown coder: "{}"'.format(k), color='red'))  # pragma: no cover

    if args.columns:
        head('Columns')
        for row in sheet.iterrows():
            for col in row:
                print(col)
            break
