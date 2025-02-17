from collections import namedtuple


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
