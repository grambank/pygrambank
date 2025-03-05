import unittest

from pygrambank import examples as gbex


class CustomLineArranger(gbex.DefaultArranger):
    """Just an example for a line arranger to run tests against."""

    @classmethod
    def is_applicable(cls, feature_id, language_id):
        return feature_id == 'feat1' and language_id == 'lang1'

    def error(self):
        if len(self.igt) < 3:
            return 'IGT needs at least 3 lines'
        else:
            return None

    def fix_igt(self, igt):
        if len(igt) > 3:
            # idk just merge excess lines into one
            return [igt[0], igt[1], ' '.join(igt[2:])]
        else:
            return igt

    def primary_text(self):
        return ' '.join(self.igt[0].split())

    def analyzed_word(self):
        return self.igt[1].split()

    def gloss(self):
        return self.igt[2].split()


class LineArrangement(unittest.TestCase):
    # Note, these tests don't really run against the 'api barrier' of line
    # arrangement but rather against the internal function called deep inside
    # the example parser.
    # Also, I kinda hate the way this works myself (with those subclasses that
    # get defined in the clfdbench and instantiated in pygrambank) but it is
    # what it is.

    def test_two_lines(self):
        igt = ['m1', 'x1']
        arranger, err = gbex.arrange_example_lines([], 'lang1', 'feat1', 1, igt)
        self.assertEqual(err, None)
        self.assertEqual(arranger.primary_text(), 'm1')
        self.assertEqual(arranger.analyzed_word(), ['m1'])
        self.assertEqual(arranger.gloss(), ['x1'])

    def test_split_glosses(self):
        igt = ['   m1   m2    ', '  x1  x2    ']
        arranger, err = gbex.arrange_example_lines([], 'lang1', 'feat1', 1, igt)
        self.assertEqual(err, None)
        self.assertEqual(arranger.primary_text(), 'm1 m2')
        self.assertEqual(arranger.analyzed_word(), ['m1', 'm2'])
        self.assertEqual(arranger.gloss(), ['x1', 'x2'])

    def test_not_enough_lines(self):
        igt = ['m1']
        arranger, err = gbex.arrange_example_lines([], 'lang1', 'feat1', 1, igt)
        self.assertTrue(isinstance(err, gbex.ParseError))
        self.assertEqual(arranger, None)

    def test_too_many_lines(self):
        igt = ['t1', 'm1', 'x1']
        arranger, err = gbex.arrange_example_lines([], 'lang1', 'feat1', 1, igt)
        self.assertEqual(bool(err), True)
        self.assertEqual(arranger, None)

    def test_apply_custom_arranger(self):
        igt1 = ['m1', 'x1']
        igt2 = ['t1', 'm1', 'x1']
        arrangers = [CustomLineArranger]
        arranger, err = gbex.arrange_example_lines(arrangers, 'not lang1', 'not feat1', 1, igt1)
        self.assertEqual(err, None)
        self.assertEqual(type(arranger), gbex.DefaultArranger)
        self.assertEqual(arranger.primary_text(), 'm1')
        self.assertEqual(arranger.analyzed_word(), ['m1'])
        self.assertEqual(arranger.gloss(), ['x1'])
        arranger, err = gbex.arrange_example_lines(arrangers, 'lang1', 'feat1', 1, igt2)
        self.assertEqual(err, None)
        self.assertEqual(type(arranger), CustomLineArranger)
        self.assertEqual(arranger.primary_text(), 't1')
        self.assertEqual(arranger.analyzed_word(), ['m1'])
        self.assertEqual(arranger.gloss(), ['x1'])

    def test_custom_error(self):
        igt = ['m1', 'x1']
        arrangers = [CustomLineArranger]
        arranger, err = gbex.arrange_example_lines(arrangers, 'lang1', 'feat1', 1, igt)
        self.assertTrue(isinstance(err, gbex.ParseError))
        self.assertEqual(arranger, None)

    def test_custom_fix(self):
        igt = ['t1', 'm1 m2 m3', 'x1', 'x2', 'x3']
        arrangers = [CustomLineArranger]
        arranger, err = gbex.arrange_example_lines(arrangers, 'lang1', 'feat1', 1, igt)
        self.assertEqual(err, None)
        self.assertEqual(arranger.primary_text(), 't1')
        self.assertEqual(arranger.analyzed_word(), ['m1', 'm2', 'm3'])
        self.assertEqual(arranger.gloss(), ['x1', 'x2', 'x3'])


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


class AlignmentFilter(unittest.TestCase):

    def test_all_aligned(self):
        examples = [
            {'Analyzed_Word': ['m1.1', 'm1.2', 'm1.3'],
             'Gloss': ['g1.1', 'g1.2', 'g1.3']},
            {'Analyzed_Word': ['m2.1', 'm2.2', 'm2.3'],
             'Gloss': ['g2.1', 'g2.2', 'g2.3']},
            {'Analyzed_Word': ['m3.1', 'm3.2', 'm3.3'],
             'Gloss': ['g3.1', 'g3.2', 'g3.3']}]
        expected = [
            {'Analyzed_Word': ['m1.1', 'm1.2', 'm1.3'],
             'Gloss': ['g1.1', 'g1.2', 'g1.3']},
            {'Analyzed_Word': ['m2.1', 'm2.2', 'm2.3'],
             'Gloss': ['g2.1', 'g2.2', 'g2.3']},
            {'Analyzed_Word': ['m3.1', 'm3.2', 'm3.3'],
             'Gloss': ['g3.1', 'g3.2', 'g3.3']}]
        result, errors = gbex.drop_misaligned(examples)
        self.assertEqual(result, expected)
        self.assertEqual(errors, [])

    def test_too_many_glosses(self):
        examples = [
            {'Analyzed_Word': ['m1.1', 'm1.2', 'm1.3'],
             'Gloss': ['g1.1', 'g1.2', 'g1.3']},
            {'Analyzed_Word': ['m2.1', 'm2.2', 'm2.3'],
             'Gloss': ['g2.1', 'g2.2', 'g2.3', 'g2.???']},
            {'Analyzed_Word': ['m3.1', 'm3.2', 'm3.3'],
             'Gloss': ['g3.1', 'g3.2', 'g3.3']}]
        expected = [
            {'Analyzed_Word': ['m1.1', 'm1.2', 'm1.3'],
             'Gloss': ['g1.1', 'g1.2', 'g1.3']},
            {'Analyzed_Word': ['m3.1', 'm3.2', 'm3.3'],
             'Gloss': ['g3.1', 'g3.2', 'g3.3']}]
        result, errors = gbex.drop_misaligned(examples)
        self.assertEqual(result, expected)
        self.assertEqual(len(errors), 1)

    def test_not_enough_glosses(self):
        examples = [
            {'Analyzed_Word': ['m1.1', 'm1.2', 'm1.3'],
             'Gloss': ['g1.1', 'g1.2', 'g1.3']},
            {'Analyzed_Word': ['m2.1', 'm2.2', 'm2.3', 'm2.???'],
             'Gloss': ['g2.1', 'g2.2', 'g2.3']},
            {'Analyzed_Word': ['m3.1', 'm3.2', 'm3.3'],
             'Gloss': ['g3.1', 'g3.2', 'g3.3']}]
        expected = [
            {'Analyzed_Word': ['m1.1', 'm1.2', 'm1.3'],
             'Gloss': ['g1.1', 'g1.2', 'g1.3']},
            {'Analyzed_Word': ['m3.1', 'm3.2', 'm3.3'],
             'Gloss': ['g3.1', 'g3.2', 'g3.3']}]
        result, errors = gbex.drop_misaligned(examples)
        self.assertEqual(result, expected)
        self.assertEqual(len(errors), 1)


class ExampleDeduplication(unittest.TestCase):

    def test_no_duplicates(self):
        examples = [
            {'ID': 'ex1',
             'Primary_Text': 'an example'},
            {'ID': 'ex2',
             'Primary_Text': 'a second example'}]
        # nothing happened
        expected = [
            {'ID': 'ex1',
             'Primary_Text': 'an example'},
            {'ID': 'ex2',
             'Primary_Text': 'a second example'}]
        result, errors = gbex.unique_examples(examples)
        self.assertEqual(errors, [])
        self.assertEqual(result, expected)

    def test_exact_duplicates(self):
        examples = [
            {'ID': 'ex1',
             'Primary_Text': 'the same example'},
            {'ID': 'ex2',
             'Primary_Text': 'the same example'}]
        expected = [
            {'ID': 'ex1',
             'Primary_Text': 'the same example'}]
        result, errors = gbex.unique_examples(examples)
        self.assertEqual(errors, [])
        self.assertEqual(result, expected)

    def test_language_matters(self):
        examples = [
            {'ID': 'ex1',
             'Language_ID': 'czec1258',
             'Primary_Text': 'dobré pivo'},
            {'ID': 'ex2',
             'Language_ID': 'slov1269',
             'Primary_Text': 'dobré pivo'}]
        expected = [
            {'ID': 'ex1',
             'Language_ID': 'czec1258',
             'Primary_Text': 'dobré pivo'},
            {'ID': 'ex2',
             'Language_ID': 'slov1269',
             'Primary_Text': 'dobré pivo'}]
        result, errors = gbex.unique_examples(examples)
        self.assertEqual(errors, [])
        self.assertEqual(result, expected)

    def test_fuzzy_duplicates(self):
        examples = [
            {'ID': 'ex1',
             'Primary_Text': 'Fast dasselbe',
             'Analyzed_Word': ['fast', 'dasselbe'],
             'Gloss': ['almost', 'the.same'],
             'Translated_Text': 'Almost the same'},
            {'ID': 'ex1',
             'Primary_Text': 'FAST dasselbe',
             'Analyzed_Word': ['fast', 'dasselbe'],
             'Gloss': ['almost', 'the.same'],
             'Translated_Text': 'Almost the same'},
            {'ID': 'ex1',
             'Primary_Text': 'Fast dasselbe',
             'Analyzed_Word': ['fast', 'das-selbe'],
             'Gloss': ['almost', 'the.same'],
             'Translated_Text': 'Almost the same'},
            {'ID': 'ex1',
             'Primary_Text': 'Fast dasselbe',
             'Analyzed_Word': ['fast', 'dasselbe'],
             'Gloss': ['almost', 'the.same'],
             'Translated_Text': 'Almost the same'},
            {'ID': 'ex1',
             'Primary_Text': 'Fast dasselbe',
             'Analyzed_Word': ['fast', 'dasselbe'],
             'Gloss': ['almost', 'the.same'],
             'Translated_Text': 'Almost(!!!) the same'}]
        expected = [
            {'ID': 'ex1',
             'Primary_Text': 'Fast dasselbe',
             'Analyzed_Word': ['fast', 'dasselbe'],
             'Gloss': ['almost', 'the.same'],
             'Translated_Text': 'Almost the same'},
            {'ID': 'ex1',
             'Primary_Text': 'FAST dasselbe',
             'Analyzed_Word': ['fast', 'dasselbe'],
             'Gloss': ['almost', 'the.same'],
             'Translated_Text': 'Almost the same'},
            {'ID': 'ex1',
             'Primary_Text': 'Fast dasselbe',
             'Analyzed_Word': ['fast', 'das-selbe'],
             'Gloss': ['almost', 'the.same'],
             'Translated_Text': 'Almost the same'},
            {'ID': 'ex1',
             'Primary_Text': 'Fast dasselbe',
             'Analyzed_Word': ['fast', 'dasselbe'],
             'Gloss': ['almost', 'the.same'],
             'Translated_Text': 'Almost the same'},
            {'ID': 'ex1',
             'Primary_Text': 'Fast dasselbe',
             'Analyzed_Word': ['fast', 'dasselbe'],
             'Gloss': ['almost', 'the.same'],
             'Translated_Text': 'Almost(!!!) the same'}]
        result, errors = gbex.unique_examples(examples)
        self.assertEqual(len(errors), 1)
        self.assertEqual(result, expected)
