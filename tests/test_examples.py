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


class ExampleExtraction(unittest.TestCase):

    def test_no_example_sections(self):
        wikipage = 'No examples here, sir'
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(examples, [])
        self.assertEqual(len(errors), 1)

    def test_too_many_example_sections(self):
        wikipage = '\n'.join([
            '## Examples',
            'hi',
            '## Examples',
            'hi again'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(examples, [])
        self.assertEqual(len(errors), 1)

    def test_other_non_example_sections(self):
        wikipage = '\n'.join([
            '## No Examples',
            'hi',
            '## Examples',
            'hi again',
            '## No Examples either',
            'how are you doing today?'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(examples, [])
        self.assertEqual(errors, [])

    def test_no_language_block(self):
        wikipage = '\n'.join([
            '## Examples',
            'hi'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(examples, [])
        self.assertEqual(errors, [])

    def test_typo_in_glottocode(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: upp1465)'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(examples, [])
        self.assertEqual(len(errors), 1)

    def test_no_examples(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(examples, [])
        self.assertEqual(len(errors), 1)

    def test_no_example_but_feature_value(self):
        # FIXME(johannes): apparently that both the last line and the next
        # section are load-bearing here.
        # They shouldn't be.
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '',
            'Coded 1.',
            '',
            '## Next section'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(examples, [])
        self.assertEqual(errors, [])

    def test_nothing_after_feature_value(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '',
            'Coded 1.'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(examples, [])
        self.assertNotEqual(errors, [])

    def test_missing_example_block(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '',
            'Coded 1.',
            '',
            'hi'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(examples, [])
        self.assertNotEqual(errors, [])

    def test_one_example(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'der  mehrt         ega',
            'DEM  take.forever  constantly',
            '‘he always takes forever’',
            '```'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(len(examples), 1)
        ex = examples[0]
        self.assertEqual(ex['Language_ID'], 'uppe1465')
        self.assertEqual(ex['Primary_Text'], 'der mehrt ega')
        self.assertEqual(ex['Analyzed_Word'], ['der', 'mehrt', 'ega'])
        self.assertEqual(ex['Gloss'], ['DEM', 'take.forever', 'constantly'])
        self.assertEqual(ex['Translated_Text'], 'he always takes forever')
        self.assertEqual(errors, [])

    def test_space_before_example(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            '',
            'der  mehrt         ega',
            'DEM  take.forever  constantly',
            '‘he always takes forever’',
            '```'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(len(examples), 1)
        ex = examples[0]
        self.assertEqual(ex['Language_ID'], 'uppe1465')
        self.assertEqual(ex['Primary_Text'], 'der mehrt ega')
        self.assertEqual(ex['Analyzed_Word'], ['der', 'mehrt', 'ega'])
        self.assertEqual(ex['Gloss'], ['DEM', 'take.forever', 'constantly'])
        self.assertEqual(ex['Translated_Text'], 'he always takes forever')
        self.assertEqual(errors, [])

    def test_unclosed_example_block(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'der  mehrt         ega',
            'DEM  take.forever  constantly',
            '‘he always takes forever’',
            '## next section'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(examples, [])
        self.assertNotEqual(errors, [])

    def test_missing_analyzed_word(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'der mehrt ega',
            '‘he always takes forever’',
            '```',
            '## next section'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(examples, [])
        self.assertEqual(len(errors), 1)

    def test_missing_igt(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            '‘he always takes forever’',
            '```',
            '## next section'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(examples, [])
        self.assertEqual(len(errors), 1)

    def test_missing_translation(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'der  mehrt         ega',
            'DEM  take.forever  constantly',
            '```',
            '## next section'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(examples, [])
        self.assertEqual(len(errors), 1)

    def test_note_before_example(self):
        wikipage = '\n'.join([
            '## Examples',
            'A random note',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'der  mehrt         ega',
            'DEM  take.forever  constantly',
            '‘he always takes forever’',
            '```'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(len(examples), 1)
        ex = examples[0]
        self.assertEqual(ex['Language_ID'], 'uppe1465')
        self.assertEqual(ex['Primary_Text'], 'der mehrt ega')
        self.assertEqual(ex['Analyzed_Word'], ['der', 'mehrt', 'ega'])
        self.assertEqual(ex['Gloss'], ['DEM', 'take.forever', 'constantly'])
        self.assertEqual(ex['Translated_Text'], 'he always takes forever')
        self.assertEqual(errors, [])

    def test_feature_value_before_example(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '',
            'Coded 1. Definitely exists.',
            '```',
            'der  mehrt         ega',
            'DEM  take.forever  constantly',
            '‘he always takes forever’',
            '```'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(len(examples), 1)
        ex = examples[0]
        self.assertEqual(ex['Language_ID'], 'uppe1465')
        self.assertEqual(ex['Primary_Text'], 'der mehrt ega')
        self.assertEqual(ex['Analyzed_Word'], ['der', 'mehrt', 'ega'])
        self.assertEqual(ex['Gloss'], ['DEM', 'take.forever', 'constantly'])
        self.assertEqual(ex['Translated_Text'], 'he always takes forever')
        self.assertEqual(errors, [])

    def test_stuff_after_translation(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'der  mehrt         ega',
            'DEM  take.forever  constantly',
            '‘he always takes forever’ (roughly)',
            '```'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(len(examples), 1)
        ex = examples[0]
        self.assertEqual(ex['Language_ID'], 'uppe1465')
        self.assertEqual(ex['Primary_Text'], 'der mehrt ega')
        self.assertEqual(ex['Analyzed_Word'], ['der', 'mehrt', 'ega'])
        self.assertEqual(ex['Gloss'], ['DEM', 'take.forever', 'constantly'])
        self.assertEqual(ex['Translated_Text'], 'he always takes forever')
        self.assertEqual(errors, [])

    def test_mulitline_translation(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'der  mehrt         ega',
            'DEM  take.forever  constantly',
            '‘he always takes…',
            '… wait for it …',
            'forever’ (wow, what a',
            'tense build-up)',
            '```'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(len(examples), 1)
        ex = examples[0]
        self.assertEqual(ex['Language_ID'], 'uppe1465')
        self.assertEqual(ex['Primary_Text'], 'der mehrt ega')
        self.assertEqual(ex['Analyzed_Word'], ['der', 'mehrt', 'ega'])
        self.assertEqual(ex['Gloss'], ['DEM', 'take.forever', 'constantly'])
        self.assertEqual(ex['Translated_Text'], 'he always takes… … wait for it … forever')
        self.assertEqual(errors, [])

    def test_multiple_quotes_in_translations(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'der  mehrt         ega',
            'DEM  take.forever  constantly',
            "‘he always takes forever’ OR ‘something else’",
            'OOOR ‘yet another thing’!',
            '```'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(len(examples), 1)
        ex = examples[0]
        self.assertEqual(ex['Language_ID'], 'uppe1465')
        self.assertEqual(ex['Primary_Text'], 'der mehrt ega')
        self.assertEqual(ex['Analyzed_Word'], ['der', 'mehrt', 'ega'])
        self.assertEqual(ex['Gloss'], ['DEM', 'take.forever', 'constantly'])
        self.assertEqual(ex['Translated_Text'], 'he always takes forever')
        # these only print two warnings
        self.assertEqual(errors, [])

    def test_multiple_examples(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'der  mehrt         ega',
            'DEM  take.forever  constantly',
            '‘he always takes forever’',
            '',
            'nu    gugge  ma,        e  Motschegiebschn',
            'well  look   for.a.bit  a  ladybird',
            '‘Would you look at that, a ladybird’',
            '```'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(len(examples), 2)
        ex1 = examples[0]
        self.assertEqual(ex1['Language_ID'], 'uppe1465')
        self.assertEqual(ex1['Primary_Text'], 'der mehrt ega')
        self.assertEqual(ex1['Analyzed_Word'], ['der', 'mehrt', 'ega'])
        self.assertEqual(ex1['Gloss'], ['DEM', 'take.forever', 'constantly'])
        self.assertEqual(ex1['Translated_Text'], 'he always takes forever')
        ex2 = examples[1]
        self.assertEqual(ex2['Language_ID'], 'uppe1465')
        self.assertEqual(ex2['Primary_Text'], 'nu gugge ma, e Motschegiebschn')
        self.assertEqual(ex2['Analyzed_Word'], ['nu', 'gugge', 'ma,', 'e', 'Motschegiebschn'])
        self.assertEqual(ex2['Gloss'], ['well', 'look', 'for.a.bit', 'a', 'ladybird'])
        self.assertEqual(ex2['Translated_Text'], 'Would you look at that, a ladybird')
        self.assertEqual(errors, [])

    def test_keep_collected_examples_on_error(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'der  mehrt         ega',
            'DEM  take.forever  constantly',
            '‘he always takes forever’',
            '',
            'nu    gugge  ma,        e  Motschegiebschn',
            '‘Would you look at that, a ladybird’',
            '```'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(len(examples), 1)
        ex1 = examples[0]
        self.assertEqual(ex1['Language_ID'], 'uppe1465')
        self.assertEqual(ex1['Primary_Text'], 'der mehrt ega')
        self.assertEqual(ex1['Analyzed_Word'], ['der', 'mehrt', 'ega'])
        self.assertEqual(ex1['Gloss'], ['DEM', 'take.forever', 'constantly'])
        self.assertEqual(ex1['Translated_Text'], 'he always takes forever')
        self.assertEqual(len(errors), 1)

    def test_strip_bullet_points(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'a.  der  mehrt         ega',
            '    DEM  take.forever  constantly',
            '    ‘he always takes forever’',
            '',
            'b.  nu    gugge  ma,        e  Motschegiebschn',
            '    well  look   for.a.bit  a  ladybird',
            '    ‘Would you look at that, a ladybird’',
            '```'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(len(examples), 2)
        ex1 = examples[0]
        self.assertEqual(ex1['Language_ID'], 'uppe1465')
        self.assertEqual(ex1['Primary_Text'], 'der mehrt ega')
        self.assertEqual(ex1['Analyzed_Word'], ['der', 'mehrt', 'ega'])
        self.assertEqual(ex1['Gloss'], ['DEM', 'take.forever', 'constantly'])
        self.assertEqual(ex1['Translated_Text'], 'he always takes forever')
        ex2 = examples[1]
        self.assertEqual(ex2['Language_ID'], 'uppe1465')
        self.assertEqual(ex2['Primary_Text'], 'nu gugge ma, e Motschegiebschn')
        self.assertEqual(ex2['Analyzed_Word'], ['nu', 'gugge', 'ma,', 'e', 'Motschegiebschn'])
        self.assertEqual(ex2['Gloss'], ['well', 'look', 'for.a.bit', 'a', 'ladybird'])
        self.assertEqual(ex2['Translated_Text'], 'Would you look at that, a ladybird')
        self.assertEqual(errors, [])

    def test_multiple_example_blocks(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'der  mehrt         ega',
            'DEM  take.forever  constantly',
            '‘he always takes forever’',
            '```',
            '',
            'Furthermore, see:',
            '',
            '```',
            'nu    gugge  ma,        e  Motschegiebschn',
            'well  look   for.a.bit  a  ladybird',
            '‘Would you look at that, a ladybird’',
            '```'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(len(examples), 2)
        ex1 = examples[0]
        self.assertEqual(ex1['Language_ID'], 'uppe1465')
        self.assertEqual(ex1['Primary_Text'], 'der mehrt ega')
        self.assertEqual(ex1['Analyzed_Word'], ['der', 'mehrt', 'ega'])
        self.assertEqual(ex1['Gloss'], ['DEM', 'take.forever', 'constantly'])
        self.assertEqual(ex1['Translated_Text'], 'he always takes forever')
        ex2 = examples[1]
        self.assertEqual(ex2['Language_ID'], 'uppe1465')
        self.assertEqual(ex2['Primary_Text'], 'nu gugge ma, e Motschegiebschn')
        self.assertEqual(ex2['Analyzed_Word'], ['nu', 'gugge', 'ma,', 'e', 'Motschegiebschn'])
        self.assertEqual(ex2['Gloss'], ['well', 'look', 'for.a.bit', 'a', 'ladybird'])
        self.assertEqual(ex2['Translated_Text'], 'Would you look at that, a ladybird')
        self.assertEqual(errors, [])

    def test_multiple_languages(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'der  mehrt         ega',
            'DEM  take.forever  constantly',
            '‘he always takes forever’',
            '```',
            '**Upper Sorbian** (Glottolog: uppe1395)',
            '```',
            'Měrćin  čita   knihu  w   bibliotece',
            'Martin  reads  book   in  library',
            '‘Martin reads a book in the library’',
            '```'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(len(examples), 2)
        ex1 = examples[0]
        self.assertEqual(ex1['Language_ID'], 'uppe1465')
        self.assertEqual(ex1['Primary_Text'], 'der mehrt ega')
        self.assertEqual(ex1['Analyzed_Word'], ['der', 'mehrt', 'ega'])
        self.assertEqual(ex1['Gloss'], ['DEM', 'take.forever', 'constantly'])
        self.assertEqual(ex1['Translated_Text'], 'he always takes forever')
        ex2 = examples[1]
        self.assertEqual(ex2['Language_ID'], 'uppe1395')
        self.assertEqual(ex2['Primary_Text'], 'Měrćin čita knihu w bibliotece')
        self.assertEqual(ex2['Analyzed_Word'], ['Měrćin', 'čita', 'knihu', 'w', 'bibliotece'])
        self.assertEqual(ex2['Gloss'], ['Martin', 'reads', 'book', 'in', 'library'])
        self.assertEqual(ex2['Translated_Text'], 'Martin reads a book in the library')
        self.assertEqual(errors, [])

    def test_blacklist(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'der  mehrt         ega',
            'DEM  take.forever  constantly',
            '‘he always takes forever’',
            '```',
            '**Upper Sorbian** (Glottolog: uppe1395)',
            '```',
            '   | SG            | DU          | PL        ',
            '---+---------------+-------------+-----------',
            ' 1 | ja            | mój         | my        ',
            ' 2 | ty            | wój         | wy        ',
            ' 3 | wón/wona/wone | wonaj/wonej | woni/wone ',
            '```'])
        blacklist = [('GB001', 'uppe1395')]
        parser = gbex.ExampleParser([], blacklist)
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(len(examples), 1)
        ex = examples[0]
        self.assertEqual(ex['Language_ID'], 'uppe1465')
        self.assertEqual(ex['Primary_Text'], 'der mehrt ega')
        self.assertEqual(ex['Analyzed_Word'], ['der', 'mehrt', 'ega'])
        self.assertEqual(ex['Gloss'], ['DEM', 'take.forever', 'constantly'])
        self.assertEqual(ex['Translated_Text'], 'he always takes forever')
        self.assertEqual(errors, [])

    def test_ignore_note_at_the_end(self):
        wikipage = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'der  mehrt         ega',
            'DEM  take.forever  constantly',
            '‘he always takes forever’',
            '',
            '(Source: dude just trust me)',
            '```'])
        parser = gbex.ExampleParser([], [])
        examples = parser.parse_description('GB001', wikipage)
        errors = parser.errors()
        self.assertEqual(len(examples), 1)
        ex = examples[0]
        self.assertEqual(ex['Language_ID'], 'uppe1465')
        self.assertEqual(ex['Primary_Text'], 'der mehrt ega')
        self.assertEqual(ex['Analyzed_Word'], ['der', 'mehrt', 'ega'])
        self.assertEqual(ex['Gloss'], ['DEM', 'take.forever', 'constantly'])
        self.assertEqual(ex['Translated_Text'], 'he always takes forever')
        self.assertEqual(errors, [])

    def test_parser_reuse_and_error_collection(self):
        parser = gbex.ExampleParser([], [])
        wikipage1 = '\n'.join([
            '## Examples',
            '**Saxon** (Glottolog: uppe1465)',
            '```',
            'a.  der  mehrt         ega',
            '    DEM  take.forever  constantly',
            '    ‘he always takes forever’',
            '',
            'b.  nu    gugge  ma,        e  Motschegiebschn',
            '    well  look   for.a.bit  a  ladybird',
            '```'])
        examples1 = parser.parse_description('GB001', wikipage1)
        wikipage2 = '\n'.join([
            '## Examples',
            '**Upper Sorbian** (Glottolog: uppe1395)',
            '```',
            'a. Měrćin  čita   knihu  w   bibliotece',
            '   Martin  reads  book   in  library',
            '   ‘Martin reads a book in the library’',
            '',
            'b. Měrćin  čita   knihu  wo     wjelrybach',
            '   Martin  reads  book   about  whales',
            '```'])
        examples2 = parser.parse_description('GB001', wikipage2)

        self.assertEqual(len(examples1), 1)
        ex1 = examples1[0]
        self.assertEqual(ex1['Language_ID'], 'uppe1465')
        self.assertEqual(ex1['Primary_Text'], 'der mehrt ega')
        self.assertEqual(ex1['Analyzed_Word'], ['der', 'mehrt', 'ega'])
        self.assertEqual(ex1['Gloss'], ['DEM', 'take.forever', 'constantly'])
        self.assertEqual(ex1['Translated_Text'], 'he always takes forever')

        self.assertEqual(len(examples2), 1)
        ex2 = examples2[0]
        self.assertEqual(ex2['Language_ID'], 'uppe1395')
        self.assertEqual(ex2['Primary_Text'], 'Měrćin čita knihu w bibliotece')
        self.assertEqual(ex2['Analyzed_Word'], ['Měrćin', 'čita', 'knihu', 'w', 'bibliotece'])
        self.assertEqual(ex2['Gloss'], ['Martin', 'reads', 'book', 'in', 'library'])
        self.assertEqual(ex2['Translated_Text'], 'Martin reads a book in the library')

        errors = parser.errors()
        self.assertEqual(len(errors), 2)


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
