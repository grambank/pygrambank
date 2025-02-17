import unittest

from pygrambank import examples as gbex


class AlignmentCorrection(unittest.TestCase):

    def test_rule_not_applicable(self):
        example = {
            'ID': 'ex1',
            'Analyzed_Word': ['m1', 'm2', 'm3'],
            'Gloss': ['g1', 'g2', 'g3'],
        }
        rule = gbex.GlossRule(
            lambda e: e['ID'] == 'not ex1', ['m1', 'm2'], ['x1', 'x2'])
        gbex.fix_glosses(example, [rule])
        # no mutation
        self.assertEqual(example['ID'], 'ex1')
        self.assertEqual(example['Analyzed_Word'], ['m1', 'm2', 'm3'])
        self.assertEqual(example['Gloss'], ['g1', 'g2', 'g3'])

    def test_example_is_zero(self):
        example = {}
        rule = gbex.GlossRule(lambda _: True, ['m1', 'm2'], ['x1', 'x2'])
        gbex.fix_glosses(example, [rule])
        # no mutation
        self.assertEqual(example, {})

    def test_rule_applies_but_does_not_match(self):
        example = {
            'ID': 'ex1',
            'Analyzed_Word': ['m1', 'm2', 'm3'],
        }
        rule = gbex.GlossRule(
            lambda e: e['ID'] == 'ex1', ['not m1', 'not m2'], ['x1', 'x2'])
        gbex.fix_glosses(example, [rule])
        # no mutation
        self.assertEqual(example['ID'], 'ex1')
        self.assertEqual(example['Analyzed_Word'], ['m1', 'm2', 'm3'])

    def test_rule_lacks_lhs(self):
        example = {
            'ID': 'ex1',
            'Analyzed_Word': ['m1', 'm2', 'm3'],
        }
        rule = gbex.GlossRule(
            lambda e: e['ID'] == 'ex1', [], ['one million euros in my bank account'])
        with self.assertRaises(gbex.MalformedRule):
            gbex.fix_glosses(example, [rule])
        # no mutation
        self.assertEqual(example['ID'], 'ex1')
        self.assertEqual(example['Analyzed_Word'], ['m1', 'm2', 'm3'])

    def test_rule_adds_items(self):
        example = {
            'ID': 'ex1',
            'Analyzed_Word': ['m1', 'm2', 'm3'],
        }
        rule = gbex.GlossRule(
            lambda e: e['ID'] == 'ex1', ['m1', 'm2'], ['m1', 'm2', 'm2.5'])
        gbex.fix_glosses(example, [rule])
        self.assertEqual(example['Analyzed_Word'], ['m1', 'm2', 'm2.5', 'm3'])
        # no mutation
        self.assertEqual(example['ID'], 'ex1')

    def test_rule_removes_items(self):
        example = {
            'ID': 'ex1',
            'Analyzed_Word': ['m1', 'm2', 'm3'],
        }
        rule = gbex.GlossRule(
            lambda e: e['ID'] == 'ex1', ['m1', 'm2'], [])
        gbex.fix_glosses(example, [rule])
        self.assertEqual(example['Analyzed_Word'], ['m3'])
        # no mutation
        self.assertEqual(example['ID'], 'ex1')

    def test_rule_transforms_items(self):
        example = {
            'ID': 'ex1',
            'Analyzed_Word': ['m1', 'm2', 'm3'],
        }
        rule = gbex.GlossRule(
            lambda e: e['ID'] == 'ex1', ['m1', 'm2'], ['x1', 'x2'])
        gbex.fix_glosses(example, [rule])
        self.assertEqual(example['Analyzed_Word'], ['x1', 'x2', 'm3'])
        # no mutation
        self.assertEqual(example['ID'], 'ex1')

    def test_rule_applies_to_glosses(self):
        example = {
            'ID': 'ex1',
            'Gloss': ['g1', 'g2', 'g3'],
        }
        rule = gbex.GlossRule(
            lambda e: e['ID'] == 'ex1', ['g1', 'g2'], ['y1', 'y2'])
        gbex.fix_glosses(example, [rule])
        self.assertEqual(example['Gloss'], ['y1', 'y2', 'g3'])
        # no mutation
        self.assertEqual(example['ID'], 'ex1')

    def test_rule_applies_to_multiple_examples(self):
        example_1 = {
            'ID': 'ex1',
            'Analyzed_Word': ['m1', 'm2', 'm3'],
        }
        example_2 = {
            'ID': 'ex2',
            'Analyzed_Word': ['m1', 'm2', 'm4'],
        }
        rule = gbex.GlossRule(
            lambda e: e['ID'] == 'ex1' or e['ID'] == 'ex2',
            ['m1', 'm2'], ['x1', 'x2'])
        gbex.fix_glosses(example_1, [rule])
        gbex.fix_glosses(example_2, [rule])
        self.assertEqual(example_1['Analyzed_Word'], ['x1', 'x2', 'm3'])
        self.assertEqual(example_2['Analyzed_Word'], ['x1', 'x2', 'm4'])
        # no mutation
        self.assertEqual(example_1['ID'], 'ex1')
        self.assertEqual(example_2['ID'], 'ex2')

    def test_multiple_rules_apply_to_example(self):
        example = {
            'ID': 'ex1',
            'Analyzed_Word': ['m1', 'm2', 'm3'],
        }
        transform_m1_m2 = gbex.GlossRule(
            lambda e: e['ID'] == 'ex1', ['m1', 'm2'], ['x1', 'x2'])
        transform_m3 = gbex.GlossRule(
            lambda e: e['ID'] == 'ex1', ['m3'], ['x3'])
        gbex.fix_glosses(example, [transform_m1_m2, transform_m3])
        self.assertEqual(example['Analyzed_Word'], ['x1', 'x2', 'x3'])
        # no mutation
        self.assertEqual(example['ID'], 'ex1')

    def test_rule_order_matters(self):
        example = {
            'ID': 'ex1',
            'Analyzed_Word': ['m1', 'm2', 'm3'],
        }
        # just a simple example for bleeding
        transform_m1_m2 = gbex.GlossRule(
            lambda e: e['ID'] == 'ex1', ['m1', 'm2'], ['x1', 'x2'])
        transform_m2 = gbex.GlossRule(
            lambda e: e['ID'] == 'ex1', ['m2'], ['not x2'])
        gbex.fix_glosses(example, [transform_m1_m2, transform_m2])
        self.assertEqual(example['Analyzed_Word'], ['x1', 'x2', 'm3'])
        # no mutation
        self.assertEqual(example['ID'], 'ex1')
