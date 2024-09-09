"""
Write merged sheets for conflict resolution
"""
import pathlib
from collections import defaultdict

from clldutils.clilib import PathType
from csvw import dsv

from pygrambank.conflicts import (
    make_conflict_sheet, prepare_row_for_conflict_detection,
)


def register(parser):
    # TODO: add argument to specify specific glottocodes
    parser.add_argument(
        '--outdir',
        default=pathlib.Path('conflicts'),
        type=PathType(type='dir', must_exist=False))


CONFLICT_SHEET_COLUMNS = [
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


def run(args):
    api = args.repos
    if not args.outdir.exists():
        args.outdir.mkdir()

    sheets_by_glottocode = defaultdict(list)
    for sheet in api.iter_sheets(quarantined=True):
        sheets_by_glottocode[sheet.glottocode].append(sheet)

    sheets_by_glottocode = {
        gc: sheets
        for gc, sheets in sheets_by_glottocode.items()
        if len(sheets) > 1}

    for gc, sheets in sheets_by_glottocode.items():
        conflict_path = args.outdir / f'{gc}.tsv'
        try:
            old_conflicts = list(dsv.reader(
                conflict_path, delimiter='\t', dicts=True))
        except IOError:
            # Just move on if there are no previous conflicts.
            old_conflicts = []

        all_sheet_rows = [
            prepare_row_for_conflict_detection(row, sheet, api)
            for sheet in sheets
            for row in sheet.iterrows()
            if row['Value']]
        new_conflicts = make_conflict_sheet(old_conflicts, all_sheet_rows)
        with dsv.UnicodeWriter(conflict_path, delimiter='\t') as w:
            w.writerow(CONFLICT_SHEET_COLUMNS)
            w.writerows(
                [row.get(col, '') for col in CONFLICT_SHEET_COLUMNS]
                for row in new_conflicts)

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
                assert sheet.path.parent == api.quarantine_dir, (
                    f'{sheet.path}: not in original_sheets or quarantine')
