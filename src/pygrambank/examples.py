import re
import unicodedata
from collections import defaultdict, namedtuple
from itertools import zip_longest

class ParseError(namedtuple('ParseError', 'msg')):
    """Error message for the example parser.

    We're doing errors-as-values here, so we can:
        a. Collect mutiple errors across.
        b. Keep going to try and parse more examples.
    """

    __slots__ = ()

    def __str__(self):
        """String representation of the error."""
        return self.msg


def example_error_msg(example, msg):
    """Add some debug infos to an error message, if available.

    'Available' here means that examples can have an optional field
    `Debug_Prefix` that will be prepended to the message.
    """
    if (debug_prefix := example.get('Debug_Prefix')):
        return f'{debug_prefix}: {msg}'
    else:
        return msg


def render_gloss(analyzed_word, gloss):
    """Return string represenation of `analyzed_word` and `gloss`."""
    widths = [
        max(len(wd), len(gl))
        for wd, gl in zip_longest(analyzed_word, gloss, fillvalue='')]
    return '  {}\n  {}'.format(
        '  '.join(wd.ljust(w) for w, wd in zip(widths, analyzed_word)),
        '  '.join(gl.ljust(w) for w, gl in zip(widths, gloss)))


# Line arrangement

class DefaultArranger:
    """Line arranger for a 'prototypical' example."""

    @classmethod
    def is_applicable(cls, feature_id, language_id):
        """Return True iff. this arranger is supposed to be used."""
        return True

    def __init__(self, feature_id, language_id, igt):
        """Accept igt."""
        self.feature_id = feature_id
        self.language_id = language_id
        self.igt = self.fix_igt(igt)

    def error(self):
        """Return error message if IGT is invalid."""
        # TODO: check for * (do we want ungrammatical examples?)
        if len(self.igt) != 2:
            return "IGT doesn't have exactly 2 lines"
        else:
            return None

    def fix_igt(self, igt):
        """Reshape the IGT before saving it."""
        return igt

    def primary_text(self):
        """Extract primary text from IGT."""
        return ' '.join(self.igt[0].split())

    def analyzed_word(self):
        """Extract analyzed word from IGT."""
        return self.igt[0].split()

    def gloss(self):
        """Extract gloss from IGT."""
        return self.igt[1].split()


def arrange_example_lines(
    line_arrangers, language_id, feature_id, example_lineno, igt,
):
    """Rearrange the lines in an interlinear gloss.

    Use the lines from the text to fill fields like Primary_Text or
    Analyzed_Word.  This needs some work because some examples have different
    numbers of lines and those lines mean different things in different
    examples, think e.g.

    (a)  Plural in German:
         alle  Menschen
         all   humans
         ‘all humans’

    vs

    (b)  alle Menschen
         all-e   Mensch-en
         all-PL  human-PL
         ‘all humans’

    This is done using custom `Arranger` objects that customise the line
    assignments.  The most common cases are handled by the `DefaultArranger`.
    """
    for cls in line_arrangers:
        if cls.is_applicable(feature_id, language_id):
            arranger_cls = cls
            break
    else:
        arranger_cls = DefaultArranger
    arranger = arranger_cls(feature_id, language_id, igt)
    if (msg := arranger.error()):
        return None, ParseError(f'{feature_id}:{example_lineno}:{language_id}: {msg}')
    else:
        return arranger, None


# Example extraction

RE_CODING_DESC = re.compile(
    r'\b(?:coded? (?:as )?|gets a )([0-3?])', re.IGNORECASE)


def is_coda(igt):
    return len(igt) == 1 and len(igt[0]) > 0 and igt[0][0] == '(' and igt[-1][-1] == ')'


NotIGT = namedtuple('NotIGT', 'feature_id language_id')


class ExampleParser:
    """Parser for extracting glossed examples from markdown.

    Grambank's example section is a complex web of implicit rules but roughly
    follows the following structure:

        ## Examples  (← example section)

        **Language** (Glottocode: xyzw1234)  (← language section)

        Coded 1.  (← optional feature value description)

        ```  (← 'source code' block containing one or more examples)
        line 1   (← gloss lines)
        line 2
        ‘translation’  (← translation wrappend in typographic single quotes ‘’)
        ```
    """

    def __init__(self, line_arrangers, blacklist):
        """Set up internal state for the example parser.

        `line_arrangers` is a list of arranger objects that reconfigure the
        lines in a glossed translation (usually a subclass of `DefaultArranger`).

        `blacklist` is a list of Feature ID–Glottocode pairs that are known to
        contain examples that don't follow the IGT structures.  Errors from
        these example blocks will not be reported.
        """
        self._reset_state()
        self._errors = []
        self.line_arrangers = line_arrangers
        self.blacklist = defaultdict(set)
        for feature_id, glottocode in blacklist:
            self.blacklist[feature_id].add(glottocode)

    def _reset_state(self):
        self.cursor = 0
        self.lines = None

    def _peek(self):
        """Return the line the parser is currently looking at."""
        try:
            return self.lines[self.cursor]
        except IndexError:
            return None

    def _consume_line(self):
        """Return the current line and then advance the cursor."""
        line = self._peek()
        self.cursor += 1
        return line

    def _skip_to(self, pred, msg):
        """Consume lines until `pred(line)` returns True."""
        while (line := self._peek()) is not None:
            if pred(line):
                return line, None
            else:
                self._consume_line()
        return None, ParseError(msg)

    def errors(self):
        """Return errors collecting duing example extraction."""
        return self._errors[:]

    def _err(self, err, blacklisted=False):
        if not blacklisted:
            self._errors.append(err)

    def parse_description(self, feature_id, description):
        """Return examples in markdown description."""
        self._reset_state()
        self.lines = unicodedata.normalize('NFC', description).strip().splitlines()
        line = None
        _, err = self._skip_to(
            lambda ln: ln == '## Examples',
            f'{feature_id}: no example section')
        if err:
            self._err(err)
            return []
        examples = self._parse_example_section(feature_id)
        while (line := self._consume_line()) is not None:
            if line == '## Examples':
                self._err(ParseError(f'{feature_id}:{self.cursor+1}: multiple example sections'))
        return examples

    def _parse_example_section(self, feature_id):
        """Return examples in the 'Examples' section."""
        line = self._consume_line()
        assert line == '## Examples', line
        examples = []
        while True:
            line, err = self._skip_to(
                lambda ln: ln.startswith(('## ', '**')),
                'eof')
            if err or line is None or line.startswith('## '):
                return examples
            elif line.startswith('**'):
                examples.extend(self._parse_language(feature_id))
            else:
                assert False, 'UNREACHABLE'  # pragma: nocover

    def _parse_language(self, feature_id):
        """Return examples in a language block."""
        line = self._consume_line()
        assert line
        m = re.fullmatch(
            r'\*\*[^*]+\*\*\s*[\([](?:ISO(?:[ -]6\d\d-3)?:\s*\S\S\S,)?\s*Glotto(?:log|code):\s*([a-z]{4}\d{4})\s*\]?\)?\.?',
            line.strip())
        if not m:
            self._err(ParseError(f'{feature_id}:{self.cursor+1}: expected one language with one glottocode: {line}'))
            return []
        language_id = m.group(1)

        line, err = self._skip_to(
            lambda ln: not ln or ln.isspace() or ln.startswith('```'),
            f'{feature_id}:{language_id}: EOF after language name')
        if err:
            self._err(err)
            return []

        examples = []
        while True:
            line, err = self._skip_to(
                lambda ln: RE_CODING_DESC.search(ln) or ln.startswith(('```', '**', '## ')),
                f'{feature_id}:{self.cursor+1}:{language_id}: expected coding description or example')
            if err:
                # if we haven't found an example, this is an error.
                # if we *do* have an example, this is just the end of the
                # language block.
                if not examples:
                    is_blacklisted = language_id in self.blacklist.get(feature_id, ())
                    self._err(err, is_blacklisted)
                break
            elif line.startswith(('**', '## ')):
                break
            elif line.startswith('```'):
                examples.extend(self._parse_example_block(feature_id, language_id))
            else:
                examples.extend(self._parse_feature_value(feature_id, language_id))
        return examples

    def _parse_feature_value(self, feature_id, language_id):
        """Return examples inside the feature description."""
        line = self._consume_line()
        assert RE_CODING_DESC.search(line)
        # TODO: check found values against actual value?
        # TODO: this section could contain sources

        # just skip the first paragraph for now
        _, err = self._skip_to(
            lambda ln: ln.startswith('```') or not ln or ln.isspace(),
            f'{feature_id}:{language_id}: EOF in coding description')
        if err:
            self._err(err)
            return []
        # skip to next block
        line, err = self._skip_to(
            lambda ln: ln.startswith(('```', '**', '## ')),
            f'{feature_id}:{language_id}: expected ``` got {line}')
        if err:
            self._err(err)
            return []
        elif line.startswith(('**', '## ')):
            return []
        elif line.startswith('```'):
            return self._parse_example_block(feature_id, language_id)
        else:
            assert False, f'UNREACHABLE: {line}'  # pragma: nocover

    def _parse_example_block(self, feature_id, language_id):
        """Find and parse example blocks."""
        line = self._consume_line()
        assert line.startswith('```')
        igt = []
        examples = []
        is_blacklisted = language_id in self.blacklist.get(feature_id, ())
        while (line := self._peek()) is not None:
            if line.startswith('```'):
                self._consume_line()
                break
            if not line or line.isspace():
                self._consume_line()
            elif re.match(r'\s*‘', line):
                example = self._parse_translation(
                    feature_id, language_id, self.cursor+1, igt,
                    is_blacklisted)
                if example:
                    examples.append(example)
                igt = []
            else:
                igt.append(self._consume_line())
        if line is None:
            self._err(
                ParseError(f'{feature_id}:{language_id}: unfinished example block'),
                is_blacklisted)
        elif igt and not is_coda(igt):
            self._err(
                ParseError(f'{feature_id}:{self.cursor+1}:{language_id}: expected translation'),
                is_blacklisted)
        return examples

    def _parse_translation(
        self, feature_id, language_id, example_lineno, igt, is_blacklisted,
    ):
        """Add translation to IGT and finalise an example."""
        line = self._peek()
        assert re.match(r'^\s*‘', line)
        line = re.sub(r'^\s*‘', '', line)
        assert line
        assert not line.isspace()
        trlines = []
        skip = False
        while line is not None:
            if line.startswith('```'):
                break
            elif not line or line.isspace():
                self._consume_line()
                line = self._peek()
                break
            elif (m := re.match(r'(.*?)’(?:$|\s)', line, flags=re.DOTALL)):
                trline = m.group(1)
                _, trend = m.span()
                # TODO: rest might contain a source
                rest = line[trend:]
                if '’' in rest:
                    print(f'{feature_id}:{self.cursor+1}:{language_id}: WARNING: multiple ’ found: {line}')
                trlines.append(trline)
                self._consume_line()
                skip = True
                line = self._peek()
            elif skip:
                self._consume_line()
                line = self._peek()
            else:
                if '’' in line:
                    print(f'{feature_id}:{self.cursor+1}:{language_id}: WARNING: unexpected ’: {line}')
                trlines.append(line)
                self._consume_line()
                line = self._peek()
        if line is None:
            self._err(
                ParseError(f'{feature_id}:{example_lineno}:{language_id} EOF in translation'),
                is_blacklisted)
            return None

        # since the first line has been asserted to be non-empty
        # there *should* be something in trlines unless I messed up
        assert trlines
        if not igt:
            self._err(
                ParseError(f'{feature_id}:{example_lineno}:{language_id}: empty example'),
                is_blacklisted)
            return None

        # remove artifacts from bulleted lists
        igt = [
            re.sub(r'^\s*(?:[a-f]\.|\([123a-e]\))\s*', '', line)
            for line in igt]

        line_arrangement, err = arrange_example_lines(
            self.line_arrangers, language_id, feature_id, example_lineno, igt)
        if err:
            self._err(err, is_blacklisted)
            return None

        translation = ' '.join(
            w
            for ln in trlines
            for w in ln.split()
            if w)
        example = {
            'Language_ID': language_id,
            'Primary_Text': line_arrangement.primary_text(),
            'Analyzed_Word': line_arrangement.analyzed_word(),
            'Gloss': line_arrangement.gloss(),
            'Translated_Text': translation.rstrip('.'),
            'Debug_Prefix': f'{feature_id}:{example_lineno}',
        }
        return example


# Transformation rules to fix misaligned glosses
#
# These rules apply after an example has been successfully parsed.  They can
# add, remove, or change items in the Analyzed_Word or Gloss of an example.
#
# Beware that transformation rule change the example *in place*.

GlossRule = namedtuple('GlossRule', 'pred lhs rhs')


class MalformedRule(Exception):
    """Error for when a user passes in an invalid rule object."""


def _apply_rule_iter(rule, items):
    index = 0
    while index < len(items):
        rule_index = 0
        while (
            rule_index < len(rule.lhs)
            and index + rule_index < len(items)
            and items[index+rule_index] == rule.lhs[rule_index]
        ):
            rule_index += 1
        if rule_index == len(rule.lhs):
            yield from rule.rhs
            index += rule_index
        else:
            yield items[index]
            index += 1


def apply_rule(rule, items):
    """Return transformed version of `items` after applying `rule` to it."""
    if not rule.lhs:
        raise MalformedRule('Left-hand-side of a transformation rule must not be empty')
    return list(_apply_rule_iter(rule, items))


def fix_glosses(example, rules):
    """Realign glosses in an `example` based on a number of `rules`.

    Note that example is mutated in place!
    """
    rules = [rule for rule in rules if rule.pred(example)]
    if not rules:
        return
    analyzed_word = example.get('Analyzed_Word')
    gloss = example.get('Gloss')
    if not analyzed_word and not gloss:
        return
    for rule in rules:
        if analyzed_word:
            analyzed_word = apply_rule(rule, analyzed_word)
        if gloss:
            gloss = apply_rule(rule, gloss)
    example['Analyzed_Word'] = analyzed_word
    example['Gloss'] = gloss


def has_aligned_glosses(example):
    """Check if glosses in an example are well-aligned."""
    return len(example['Analyzed_Word']) == len(example['Gloss'])


class AlignmentChecker:
    """Object for checking whether glossed examples are properly aligned.

    The only reason this is an object instead of a function is so we can collect
    errors messages along the way.
    """

    def __init__(self):
        """Initialise the alignment checker."""
        self._errors = []

    def errors(self):
        """Return errors collected during alignment checking."""
        return self._errors[:]

    def is_aligned(self, example):
        """Return True iff. the glosses are properly aligned.

        Return False otherwise.
        """
        if has_aligned_glosses(example):
            return True
        else:
            err = ParseError(example_error_msg(
                example,
                'misaligned glosses:\n{}'.format(
                    render_gloss(example['Analyzed_Word'], example['Gloss']))))
            self._errors.append(err)
            return False


def drop_misaligned(examples):
    """Return list of examples with well-aligned glosses."""
    checker = AlignmentChecker()
    examples = [ex for ex in examples if checker.is_aligned(ex)]
    return examples, checker.errors()


# Example deduplication
#
# This tries to detect and consolidated.  Note that the *detection* is quite
# fuzzy but the *consolidation* requires examples to match exactly.  For
# examples which pass the fuzzy match but not the exact match, errors will be
# emitted.

def _get_unique_example_ids(examples):
    unique = set()
    errors = []

    duplicates = defaultdict(list)
    for example in examples:
        primary_norm = ''.join(
            c.lower()
            for c in unicodedata.normalize('NFKD', example['Primary_Text'])
            if c.isascii() and not c.isspace())
        duplicates[example.get('Language_ID', ''), primary_norm].append(example)

    for dups in duplicates.values():
        if len(dups) < 2:
            unique.update(ex['ID'] for ex in dups)
        else:
            not_duplicates = {}
            for ex in dups:
                key = (ex['Primary_Text'],
                       ' '.join(ex.get('Analyzed_Word') or ()),
                       ' '.join(ex.get('Gloss') or ()),
                       ex.get('Translated_Text', ''))
                if key not in not_duplicates:
                    not_duplicates[key] = ex
            if len(not_duplicates) != 1:
                example_list = '\n'.join(
                    example_error_msg(ex, "\n  {}{}\n  '{}'".format(
                        ex['Primary_Text'],
                        '\n{}'.format(render_gloss(ex['Analyzed_Word'], ex['Gloss'])) if ex.get('Gloss') else '',
                        ex['Translated_Text']))
                    for ex in dups)
                # XXX: maybe return different error type?
                errors.append(ParseError(f'Possible example dups:\n{example_list}'))
            unique.update(ex['ID'] for ex in not_duplicates.values())

    return unique, errors


def unique_examples(examples):
    """Return list of *unique* examples and a list of *potential* duplicates."""
    unique_ids, errors = _get_unique_example_ids(examples)
    if len(unique_ids) != len(examples):
        examples = [ex for ex in examples if ex['ID'] in unique_ids]
    return examples, errors
