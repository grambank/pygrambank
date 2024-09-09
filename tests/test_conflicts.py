import unittest
from pygrambank import conflicts as c


class AddingValues(unittest.TestCase):

    def test_unseen_feature(self):
        old_conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': False,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20 (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20',
             'Warnings': ''},
        ]
        sheet_rows = [
            c.PotentialConflict(
                sheet_row={
                    'Feature_ID': 'GB021',
                    'Value': '21',
                    'Source': 'source21 (p.c.)',
                    'Comment': 'comment21',
                    'Contributed_Datapoint': 'XYZ',
                },
                sheet_name='ABC_abcd1234',
                warnings=''),
        ]
        expected = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': False,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20 (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20',
             'Warnings': ''},
            {'Feature_ID': 'GB021',
             'Value': '21',
             'Conflict': False,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source21 (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment21',
             'Warnings': ''},
        ]
        new_conflicts = c.make_conflict_sheet(old_conflicts, sheet_rows)
        self.assertEqual(new_conflicts, expected)

    def test_compatible_value_for_existing_feature(self):
        old_conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': False,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20 (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20',
             'Warnings': ''},
        ]
        sheet_rows = [
            c.PotentialConflict(
                sheet_row={
                    'Feature_ID': 'GB020',
                    'Value': '20',
                    'Source': 'source20b (p.c.)',
                    'Comment': 'comment20b',
                    'Contributed_Datapoint': 'XYZ',
                },
                sheet_name='DEF_abcd1234',
                warnings=''),
        ]
        expected = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': False,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20 (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': False,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        new_conflicts = c.make_conflict_sheet(old_conflicts, sheet_rows)
        self.assertEqual(new_conflicts, expected)

    def test_conflicting_value_for_conflicting_feature(self):
        old_conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': False,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20 (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20',
             'Warnings': ''},
        ]
        sheet_rows = [
            c.PotentialConflict(
                sheet_row={
                    'Feature_ID': 'GB020',
                    'Value': 'NOT 20',
                    'Source': 'source20b (p.c.)',
                    'Comment': 'comment20b',
                    'Contributed_Datapoint': 'XYZ',
                },
                sheet_name='DEF_abcd1234',
                warnings=''),
        ]
        expected = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20 (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        new_conflicts = c.make_conflict_sheet(old_conflicts, sheet_rows)
        self.assertEqual(new_conflicts, expected)

    def test_conflicting_value_for_selected_feature(self):
        old_conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': 'overconfident',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20 (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'ALSO NOT 20',
             'Conflict': True,
             'Classification of conflict': 'correct',
             'Select': 'TRUE',
             'Sheet': 'GHI_abcd1234',
             'Source': 'source20c (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20c',
             'Warnings': ''},
        ]
        sheet_rows = [
            c.PotentialConflict(
                sheet_row={
                    'Feature_ID': 'GB020',
                    'Value': 'NOT 20',
                    'Source': 'source20b (p.c.)',
                    'Comment': 'comment20b',
                    'Contributed_Datapoint': 'XYZ',
                },
                sheet_name='DEF_abcd1234',
                warnings=''),
        ]
        expected = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': 'overconfident',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20 (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20b',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'ALSO NOT 20',
             'Conflict': True,
             'Classification of conflict': 'correct',
             'Select': '',
             'Sheet': 'GHI_abcd1234',
             'Source': 'source20c (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20c',
             'Warnings': ''},
        ]
        new_conflicts = c.make_conflict_sheet(old_conflicts, sheet_rows)
        self.assertEqual(new_conflicts, expected)

    def test_compatible_value_for_selected_feature(self):
        old_conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': 'overconfident',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20 (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': True,
             'Classification of conflict': 'correct',
             'Select': 'TRUE',
             'Sheet': 'GHI_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        sheet_rows = [
            c.PotentialConflict(
                sheet_row={
                    'Feature_ID': 'GB020',
                    'Value': 'NOT 20',
                    'Source': 'source20c (p.c.)',
                    'Comment': 'comment20c',
                    'Contributed_Datapoint': 'UVW',
                },
                sheet_name='DEF_abcd1234',
                warnings=''),
        ]
        expected = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': 'overconfident',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20 (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20c (p.c.)',
             'Contributed_Datapoint': 'UVW',
             'Comment': 'comment20c',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': True,
             'Classification of conflict': 'correct',
             'Select': '',
             'Sheet': 'GHI_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        new_conflicts = c.make_conflict_sheet(old_conflicts, sheet_rows)
        self.assertEqual(new_conflicts, expected)


class UpdatingValues(unittest.TestCase):

    def test_compatible_value_for_nonconflicting_feature(self):
        old_conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': False,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': False,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        sheet_rows = [
            c.PotentialConflict(
                sheet_row={
                    'Feature_ID': 'GB020',
                    'Value': '20',
                    'Source': 'source20c (p.c.)',
                    'Comment': 'comment20c',
                    'Contributed_Datapoint': 'JKL',
                },
                sheet_name='DEF_abcd1234',
                warnings=''),
        ]
        expected = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': False,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': False,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20c (p.c.)',
             'Contributed_Datapoint': 'JKL UVW',
             'Comment': 'comment20c',
             'Warnings': ''},
        ]
        new_conflicts = c.make_conflict_sheet(old_conflicts, sheet_rows)
        self.assertEqual(new_conflicts, expected)

    def test_compatible_value_for_conflicting_feature(self):
        old_conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': False,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': False,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        sheet_rows = [
            c.PotentialConflict(
                sheet_row={
                    'Feature_ID': 'GB020',
                    'Value': 'NOT 20',
                    'Source': 'source20c (p.c.)',
                    'Comment': 'comment20c',
                    'Contributed_Datapoint': 'JKL',
                },
                sheet_name='DEF_abcd1234',
                warnings=''),
        ]
        expected = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': '',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'DEF UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20c (p.c.)',
             'Contributed_Datapoint': 'JKL',
             'Comment': 'comment20c',
             'Warnings': ''},
        ]
        new_conflicts = c.make_conflict_sheet(old_conflicts, sheet_rows)
        self.assertEqual(new_conflicts, expected)

    def test_conflicting_value_for_nonconflicting_feature(self):
        old_conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        sheet_rows = [
            c.PotentialConflict(
                sheet_row={
                    'Feature_ID': 'GB020',
                    'Value': '20',
                    'Source': 'source20c (p.c.)',
                    'Comment': 'comment20c',
                    'Contributed_Datapoint': 'JKL',
                },
                sheet_name='DEF_abcd1234',
                warnings=''),
        ]
        # This confused me for a second:
        # If updating a conflicting value would make the conflict disappear in
        # theory, it doesn't actually disappear in practice.  The reason being
        # that the old conflicting value will still be preserved as a sheet-less
        # row, i.e. there is still a conflict even if the 'physical' sheets
        # agree.
        expected = [
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': '',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'DEF UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20c (p.c.)',
             'Contributed_Datapoint': 'JKL',
             'Comment': 'comment20c',
             'Warnings': ''},
        ]
        new_conflicts = c.make_conflict_sheet(old_conflicts, sheet_rows)
        self.assertEqual(new_conflicts, expected)

    def test_conflicting_value_for_conflicting_feature(self):
        old_conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        sheet_rows = [
            c.PotentialConflict(
                sheet_row={
                    'Feature_ID': 'GB020',
                    'Value': 'ALSO NOT 20',
                    'Source': 'source20c (p.c.)',
                    'Comment': 'comment20c',
                    'Contributed_Datapoint': 'JKL',
                },
                sheet_name='DEF_abcd1234',
                warnings=''),
        ]
        expected = [
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': '',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'DEF UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'ALSO NOT 20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20c (p.c.)',
             'Contributed_Datapoint': 'JKL',
             'Comment': 'comment20c',
             'Warnings': ''},
        ]
        new_conflicts = c.make_conflict_sheet(old_conflicts, sheet_rows)
        self.assertEqual(new_conflicts, expected)

    def test_compatible_value_for_selected_feature(self):
        old_conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': 'correct',
             'Select': 'TRUE',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': True,
             'Classification of conflict': 'overconfident',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        sheet_rows = [
            c.PotentialConflict(
                sheet_row={
                    'Feature_ID': 'GB020',
                    'Value': '20',
                    'Source': 'source20c (p.c.)',
                    'Comment': 'comment20c',
                    'Contributed_Datapoint': 'JKL',
                },
                sheet_name='DEF_abcd1234',
                warnings=''),
        ]
        expected = [
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': True,
             'Classification of conflict': 'overconfident',
             'Select': '',
             'Sheet': '',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'DEF UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': 'correct',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20c (p.c.)',
             'Contributed_Datapoint': 'JKL',
             'Comment': 'comment20c',
             'Warnings': ''},
        ]
        new_conflicts = c.make_conflict_sheet(old_conflicts, sheet_rows)
        self.assertEqual(new_conflicts, expected)

    def test_conflicting_value_for_selected_feature(self):
        old_conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': 'correct',
             'Select': 'TRUE',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': True,
             'Classification of conflict': 'overconfident',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        sheet_rows = [
            c.PotentialConflict(
                sheet_row={
                    'Feature_ID': 'GB020',
                    'Value': 'ALSO NOT 20',
                    'Source': 'source20c (p.c.)',
                    'Comment': 'comment20c',
                    'Contributed_Datapoint': 'JKL',
                },
                sheet_name='DEF_abcd1234',
                warnings=''),
        ]
        expected = [
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': True,
             'Classification of conflict': 'overconfident',
             'Select': '',
             'Sheet': '',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'DEF UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': True,
             'Classification of conflict': 'correct',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'ALSO NOT 20',
             'Conflict': True,
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20c (p.c.)',
             'Contributed_Datapoint': 'JKL',
             'Comment': 'comment20c',
             'Warnings': ''},
        ]
        new_conflicts = c.make_conflict_sheet(old_conflicts, sheet_rows)
        self.assertEqual(new_conflicts, expected)


class ConflictChecks(unittest.TestCase):

    def test_happy_path(self):
        conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': 'True',
             'Classification of conflict': 'overconfident',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': 'True',
             'Classification of conflict': 'correct',
             'Select': 'TRUE',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        _, errors = c.check_conflicts(conflicts)
        self.assertEqual(errors, [])

    def test_rows_must_agree_on_the_fact_theyre_conflicting(self):
        conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': 'False',
             'Classification of conflict': 'overconfident',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': 'True',
             'Classification of conflict': 'correct',
             'Select': 'TRUE',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        _, errors = c.check_conflicts(conflicts)
        self.assertEqual(errors, ["GB020: 'Conflict' columns must all be True or all be False"])

    def test_nothing_selected(self):
        conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': 'True',
             'Classification of conflict': 'overconfident',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': 'True',
             'Classification of conflict': 'overconfident',
             'Select': '',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        _, errors = c.check_conflicts(conflicts)
        self.assertEqual(errors, ['No selected row for GB020'])

    def test_selected_rows_must_agree_on_value(self):
        conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': 'True',
             'Classification of conflict': 'correct',
             'Select': 'TRUE',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': 'True',
             'Classification of conflict': 'correct',
             'Select': 'TRUE',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        _, errors = c.check_conflicts(conflicts)
        self.assertEqual(errors, ['Different values selected for GB020'])

    def test_rows_need_to_be_classified(self):
        conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': 'True',
             'Classification of conflict': '',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': 'True',
             'Classification of conflict': 'correct',
             'Select': 'TRUE',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        _, errors = c.check_conflicts(conflicts)
        self.assertEqual(errors, ['Missing classifcation for GB020'])

    def test_rows_must_used_predefined_classifications(self):
        conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': 'True',
             'Classification of conflict': 'NOT A KNOWN TAG',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': 'True',
             'Classification of conflict': 'correct',
             'Select': 'TRUE',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        _, errors = c.check_conflicts(conflicts)
        self.assertEqual(errors, ['Invalid classification for GB020: not a known tag'])

    def test_selected_row_must_be_classified_as_correct(self):
        conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': 'True',
             'Classification of conflict': 'overconfident',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': 'True',
             'Classification of conflict': 'true',
             'Select': 'TRUE',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        _, errors = c.check_conflicts(conflicts)
        self.assertEqual(errors, ['Selected row not classified as correct for GB020'])

    def test_selected_row_must_have_attribution(self):
        conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': 'True',
             'Classification of conflict': 'overconfident',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': 'True',
             'Classification of conflict': 'correct',
             'Select': 'TRUE',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': '',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        _, errors = c.check_conflicts(conflicts)
        self.assertEqual(errors, ['Selected row has no coder specified in Contributed_Datapoint'])

    def test_correct_values_must_not_conflict(self):
        conflicts = [
            {'Feature_ID': 'GB020',
             'Value': '20',
             'Conflict': 'True',
             'Classification of conflict': 'correct',
             'Select': '',
             'Sheet': 'ABC_abcd1234',
             'Source': 'source20a (p.c.)',
             'Contributed_Datapoint': 'XYZ',
             'Comment': 'comment20a',
             'Warnings': ''},
            {'Feature_ID': 'GB020',
             'Value': 'NOT 20',
             'Conflict': 'True',
             'Classification of conflict': 'correct',
             'Select': 'TRUE',
             'Sheet': 'DEF_abcd1234',
             'Source': 'source20b (p.c.)',
             'Contributed_Datapoint': 'UVW',
             'Comment': 'comment20b',
             'Warnings': ''},
        ]
        _, errors = c.check_conflicts(conflicts)
        self.assertEqual(errors, [
            'Row classified as correct, but value is different'
            ' from selected value for GB020'])
