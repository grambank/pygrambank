"""
Write merged sheets for conflict resolution
"""
import pathlib
from itertools import chain
from collections import defaultdict

from clldutils.clilib import PathType
from csvw import dsv

from pygrambank.sheet import Row


def register(parser):
    parser.add_argument(
        '--outdir', default=pathlib.Path('.'), type=PathType(type='dir', must_exist=False))


class Warnings:
    def __init__(self):
        # Accumulator for warning messages:
        self.messages = ''

    def __call__(self, msg, lineno, level=None, row_=None, **kw):
        # This will be called within Sheet.valid_row when problems are detected.
        self.messages += '\n{}:{}: {}'.format(level, row_['Feature_ID'], msg)


def make_conflict_row(sheet_row, sheet, api):
    # See what "grambank check" would do with the row:
    warnings = Warnings()
    sheet.valid_row(sheet_row, api, log=warnings)
    return {
        'Feature_ID': sheet_row['Feature_ID'],
        'Value': sheet_row['Value'],
        'Conflict': False,
        'Classification of conflict': '',
        'Select': '',
        'Sheet': sheet.path.stem,
        'Source': sheet_row.get('Source', ''),
        'Contributed_Datapoint': ' '.join(
            Row.from_dict(sheet_row).contributed_datapoint),
        'Comment': sheet_row.get('Comment', ''),
        'Warnings': warnings.messages,
    }


def make_conflict_sheet(path, sheets, api):
    if len(sheets) < 2:
        return

    conflicts = defaultdict(lambda: defaultdict(list))
    try:
        for row in dsv.reader(path, delimiter='\t', dicts=True):
            conflicts[row['Feature_ID']][row['Sheet']].append(row)
    except IOError:
        # if there is no previous conflict sheet, just move on
        pass

    # checking assumptions:
    # There is only one row per sheet per feature, unless the sheet name is
    # empty.
    for feature_id, by_sheet in conflicts.items():
        for sheet_name, rows in by_sheet.items():
            assert not sheet_name or len(rows) == 1, f'{sheet_name}:{feature_id}'

    new_conflicts = (
        make_conflict_row(row, sheet, api)
        for sheet in sheets
        for row in sheet.iterrows()
        if row['Value'])

    field_updates = ['Comment', 'Source', 'Warnings']

    # FIXME: all of this horrible btw
    for new_row in new_conflicts:
        if (by_sheet := conflicts.get(new_row['Feature_ID'])):
            if (sheet_rows := by_sheet.get(new_row['Sheet'])):
                sheet_row = sheet_rows[0]
                if sheet_row['Value'] == new_row['Value']:
                    # if the value hasn't changed, update other info in the row
                    for k in field_updates:
                        sheet_row[k] = new_row[k]
                    contributors = sorted(set(chain(
                        sheet_row['Contributed_Datapoint'].split(),
                        new_row['Contributed_Datapoint'].split())))
                else:
                    # if the value has changed, move the old value to the custom
                    # sheet-less answers and put the new value in its place
                    contributors = sheet_row['Sheet']\
                        .split('_')[0]\
                        .split('-')
                    contributors.extend(
                        sheet_row['Contributed_Datapoint'].split())
                    sheet_row['Contributed_Datapoint'] = ' '.join(
                        sorted(set(contributors)))
                    sheet_row['Sheet'] = ''
                    by_sheet[''].append(sheet_row)
                    by_sheet[new_row['Sheet']] = [new_row]
                    # we have a new contender for selected new_row
                    for sheet_rows in by_sheet.values():
                        for sheet_row in sheet_rows:
                            sheet_row['Select'] = ''
            else:
                # we have a new contender for selected row
                for sheet_rows in by_sheet.values():
                    for sheet_row in sheet_rows:
                        sheet_row['Select'] = ''
                by_sheet[new_row['Sheet']].append(new_row)
        else:
            # ooh, an entirely new data point
            conflicts[new_row['Feature_ID']][new_row['Sheet']].append(new_row)

    # detect if values are conflicting
    for by_sheet in conflicts.values():
        value_count = len({
            row['Value']
            for rows in by_sheet.values()
            for row in rows})
        if value_count == 1:
            for sheet_rows in by_sheet.values():
                for sheet_row in sheet_rows:
                    sheet_row['Conflict'] = False
        else:
            for sheet_rows in by_sheet.values():
                for sheet_row in sheet_rows:
                    # preserve other values like `True (inactive feature)`
                    if not sheet_row['Conflict'] or sheet_row['Conflict'] == 'False':
                        sheet_row['Conflict'] = True

    new_conflict_sheet = [
        row
        for by_sheet in conflicts.values()
        for rows in by_sheet.values()
        for row in rows]
    new_conflict_sheet.sort(key=lambda r: (r['Feature_ID'], r['Sheet']))

    output_columns = [
        'Feature_ID',
        'Value',
        'Conflict',
        'Classification of conflict',
        'Select',
        'Sheet',
        'Source',
        'Contributed_Datapoint',
        'Comment',
        'Warnings',
    ]
    with dsv.UnicodeWriter(path, delimiter='\t') as w:
        w.writerow(output_columns)
        w.writerows(
            [row.get(col, '') for col in output_columns]
            for row in new_conflict_sheet)


def run(args):
    api = args.repos
    if not args.outdir.exists():
        args.outdir.mkdir()

    sheets_by_glottocode = defaultdict(list)
    for sheet in api.iter_sheets(quarantined=True):
        sheets_by_glottocode[sheet.glottocode].append(sheet)

    for gc, sheets in sheets_by_glottocode.items():
        make_conflict_sheet(args.outdir / f'{gc}.tsv', sheets, api)

    # Move conflicting sheets into the quarantine folder
    for sheets in sheets_by_glottocode.values():
        if len(sheets) < 2:
            continue
        for sheet in sheets:
            if sheet.path.parent == api.sheets_dir:
                new_path = api.quarantine_dir / sheet.path.name
                if new_path.exists():
                    raise IOError(f'{new_path}: already exists')
                sheet.path.rename(new_path)
            else:
                assert sheet.path.parent == api.quarantine_dir, f'{sheet.path}: not in original_sheets or quarantine'
