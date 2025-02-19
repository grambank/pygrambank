import unicodedata
from collections import defaultdict, namedtuple
from itertools import zip_longest


class ParseError(namedtuple('ParseError', 'msg')):
    def __str__(self):
        return self.msg


def example_error_msg(example, msg):
    if (debug_info := example.get('Debug_Info')):
        return f'{debug_info}: {msg}'
    else:
        return msg


def render_gloss(analyzed_word, gloss):
    widths = [
        max(len(wd), len(gl))
        for wd, gl in zip_longest(analyzed_word, gloss, fillvalue='')]
    return '  {}\n  {}'.format(
        '  '.join(wd.ljust(w) for w, wd in zip(widths, analyzed_word)),
        '  '.join(gl.ljust(w) for w, gl in zip(widths, gloss)))


# Transformation rules to fix misaligned glosses
#
# These rules apply after an example has been successfully parsed.  They can
# add, remove, or change items in the Analyzed_Word or Gloss of an example.
#
# Beware that transformation rule change the example *in place*.

GlossRule = namedtuple('GlossRule', 'pred lhs rhs')


class MalformedRule(Exception):
    pass


def apply_rule_iter(items, rule):
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


def apply_rule(items, rule):
    if not rule.lhs:
        raise MalformedRule('Left-hand-side of a transformation rule must not be empty')
    return list(apply_rule_iter(items, rule))


def fix_glosses(example, rules):
    rules = [rule for rule in rules if rule.pred(example)]
    if not rules:
        return
    analyzed_word = example.get('Analyzed_Word')
    gloss = example.get('Gloss')
    if not analyzed_word and not gloss:
        return
    for rule in rules:
        if analyzed_word:
            analyzed_word = apply_rule(analyzed_word, rule)
        if gloss:
            gloss = apply_rule(gloss, rule)
    example['Analyzed_Word'] = analyzed_word
    example['Gloss'] = gloss


def has_aligned_glosses(example):
    return len(example['Analyzed_Word']) == len(example['Gloss'])


class AlignmentChecker:
    def __init__(self):
        self.errors = []

    def is_aligned(self, example):
        if has_aligned_glosses(example):
            return True
        else:
            err = ParseError(example_error_msg(
                example,
                'misaligned glosses:\n{}'.format(
                    render_gloss(example['Analyzed_Word'], example['Gloss']))))
            self.errors.append(err)
            return False


def drop_misaligned(examples):
    checker = AlignmentChecker()
    examples = [ex for ex in examples if checker.is_aligned(ex)]
    return examples, checker.errors


# Example deduplication
#
# This tries to detect and consolidated.  Note that the *detection* is quite
# fuzzy but the *consolidation* requires examples to match exactly.  For
# examples which pass the fuzzy match but not the exact match, errors will be
# emitted.

def get_unique_example_ids(examples):
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
    unique_ids, errors = get_unique_example_ids(examples)
    if len(unique_ids) != len(examples):
        examples = [ex for ex in examples if ex['ID'] in unique_ids]
    return examples, errors
