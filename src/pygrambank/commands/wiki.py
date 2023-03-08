"""
Do we want to recode the wiki pages in CLDF markdown?
It would seem that this may add a nice IGT example/reference collection.

Also, a global references section for all wiki articles might be nice?
"""
import collections

from fuzzywuzzy import fuzz


def iter_examples(s):
    #
    # FIXME: must also parse the last mentioned Glottocode before each example!
    #
    def split_examples(ss):
        for ee in ss.split('\n\n'):
            ee = ee.strip()
            if ee:
                yield ee

    in_example, ex = False, []
    for line in s.split('\n'):
        line = line.strip()

        if line.startswith('```'):
            if in_example:
                yield from split_examples('\n'.join(ex))
                ex = []
            in_example = not in_example
        else:
            if in_example:
                ex.append(line)


def run(args):
    sections = collections.Counter()
    refs = []
    for feature in args.repos.features.values():
        sections.update(list(feature.wiki))
        for line in feature.wiki.get('References', '').split('\n'):
            line = line.strip()
            if line:
                refs.append(line)
        for line in feature.wiki.get('Further reading', '').split('\n'):
            line = line.strip()
            if line:
                refs.append(line)

        continue
        for ex in iter_examples(feature.wiki['Examples']):
            if len(ex.split('\n')) != 3:
                print(feature.id)
                break

    c, prev = 0, ''
    for ref in sorted(refs):
        if fuzz.token_set_ratio(prev, ref) < 100:
            print(ref)
            print('')
            c += 1
        prev = ref
