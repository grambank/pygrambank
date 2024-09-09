from itertools import chain, groupby
from collections import defaultdict, namedtuple

from pygrambank.sheet import Row


# CONFLICT SHEET CREATION

PotentialConflict = namedtuple(
    'PotentialConflict', 'sheet_row sheet_name warnings')


def prepare_row_for_conflict_detection(sheet_row, sheet, api):  # pragma: no cover
    assert sheet_row.get('Value')
    warnings = Warnings()
    sheet.valid_row(sheet_row, api, log=warnings)
    return PotentialConflict(
        sheet_row=sheet_row,
        sheet_name=sheet.path.stem,
        warnings=warnings.messages)


class Warnings:  # pragma: no cover
    """Mocks the logging system to capture error messages."""

    def __init__(self):
        # Accumulator for warning messages:
        self.messages = ''

    def __call__(self, msg, lineno, level=None, row_=None, **kw):
        # This will be called within Sheet.valid_row when problems are detected.
        self.messages += '\n{}:{}: {}'.format(level, row_['Feature_ID'], msg)


def make_conflict_sheet(old_conflicts, potential_conflicts):
    conflicts = defaultdict(lambda: defaultdict(list))
    for row in old_conflicts:
        conflicts[row['Feature_ID']][row['Sheet']].append(row)

    # checking assumptions:
    # There is only one conflict row per sheet per feature, unless the sheet
    # name is empty.
    for feature_id, by_sheet in conflicts.items():
        for sheet_name, rows in by_sheet.items():
            assert not sheet_name or len(rows) == 1, f'{sheet_name}:{feature_id}'

    new_conflicts = (
        make_conflict_row(row, sheet_name, warnings)
        for row, sheet_name, warnings in potential_conflicts)

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
                    sheet_row['Contributed_Datapoint'] = ' '.join(
                        sorted(set(contributors)))
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

    return new_conflict_sheet


def make_conflict_row(sheet_row, sheet_name, warnings):
    assert sheet_row.get('Value')
    # See what "grambank check" would do with the row:
    return {
        'Feature_ID': sheet_row['Feature_ID'],
        'Value': sheet_row['Value'],
        'Conflict': False,
        'Classification of conflict': '',
        'Select': '',
        'Sheet': sheet_name,
        'Source': sheet_row.get('Source', ''),
        'Contributed_Datapoint': ' '.join(
            Row.from_dict(sheet_row).contributed_datapoint),
        'Comment': sheet_row.get('Comment', ''),
        'Warnings': warnings,
    }


# CONFLICT SHEET VALIDATION

CONFLICT_CATEGORIES = {
    'correct': 'this is the correct value for this datapoint',
    'typo': 'there is no apparent reason, given the source(s) and the comment the inaccurate '
            'coding appears to be a typo',
    'overcautious': '',
    'overconfident': '',
    'new source was consulted in other coding': '',
    'feature interpretation': "the different coders have interpreted the feature differently "
                              "(some perhaps coded outside of the project and weren't in the "
                              "loop with the specifics)",
    'source interpretation': "the different coders have interpreted the source(s) differently",
    'sources disagree': '',
    'missed': "some coders have missed a section in a source",
    'less thorough coding': "the other coder(s) were particularly thorough and spotted "
                            "something that could easily have been missed or contacted expert(s)",
    'hard to code': "the language phenomena is difficult to neatly fit into the questionnaire "
                    "and took considerable discussion to resolve",
    'unclear': "it is not clear why there is a conflict",
}


def check_conflicts(sheet_rows):
    errors = []
    conflict_count = 0

    for fid, rows in groupby(
        sorted(sheet_rows, key=lambda r: r['Feature_ID']),
        lambda r: r['Feature_ID'],
    ):
        rows = list(map(make_check_row, rows))
        is_conflict = {r.conflict for r in rows}
        if len(is_conflict) != 1:
            # TODO: test
            errors.append(f"{fid}: 'Conflict' columns must all be True or all be False")
        elif next(iter(is_conflict)) == 'true':
            # For every set of same features where there is "True" for conflict, at least one should
            # have "True" in the col "Select"
            if not any(r.selected == 'true' for r in rows):
                errors.append(f'No selected row for {fid}')

            selected_value = {r.row['Value'] for r in rows if r.selected == 'true'}
            if len(selected_value) > 1:
                errors.append(f'Different values selected for {fid}')

            for row, _, selected, category in rows:
                # For every feature where there is "True" for conflict and not "True" for "Select",
                # there should be something in the col "classification of conflict" that comes
                # from this specific list
                if selected != 'true':
                    if not category:
                        errors.append(f'Missing classifcation for {fid}')
                    elif category not in CONFLICT_CATEGORIES:
                        errors.append(f'Invalid classification for {fid}: {category}')

                # Every feature which is True for select should also have "Correct" in
                # "classification of conflict"
                if selected == 'true':
                    if category != 'correct':
                        errors.append(f'Selected row not classified as correct for {fid}')
                    if not row['Contributed_Datapoint']:
                        errors.append('Selected row has no coder specified in Contributed_Datapoint')

                # Every feature where there is "True" for conflict and "Correct" in
                # "classification of conflict" but nothing in "Select" should have the same Value
                # as whichever row has "Select" =" True in that set of features for that language
                # (this only comes into effect if there is a comparison
                # of more than 2 sheets and one row happens to be better Comment or Source-wise).
                if category == 'correct' and selected != 'true':
                    if row['Value'] not in selected_value:
                        errors.append(
                            'Row classified as correct, but value is different'
                            f' from selected value for {fid}')

            conflict_count += 1

    return conflict_count, errors


CheckRow = namedtuple('CheckRow', 'row conflict selected classification')


def make_check_row(sheet_row):
    return CheckRow(
        row=sheet_row,
        conflict=sheet_row['Conflict'].strip().lower(),
        selected=sheet_row['Select'].strip().lower(),
        classification=sheet_row['Classification of conflict'].strip().lower())


# TODO: move and test ad-hoc merge
# TODO: move and test actual merge
