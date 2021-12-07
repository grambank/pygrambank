"""
"""
import itertools

from csvw.dsv import reader
from clldutils.clilib import PathType


def register(parser):
    parser.add_argument('sheet', type=PathType(type='file'))


classes = {
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


def norm(r, k):
    return r[k].strip().lower()


def check(sheet, log=None):
    ok = True
    conflicts = 0

    def error(msg):
        if log:
            log.error(msg)
        return False

    for fid, rows in itertools.groupby(
            sorted(reader(sheet, dicts=True, delimiter='\t'), key=lambda r: r['Feature_ID']),
            lambda r: r['Feature_ID'],
    ):
        rows = [(r, norm(r, 'Conflict'), norm(r, 'Select'), norm(r, 'Classification of conflict'))
                for r in rows]
        if all(r[1] == 'true' for r in rows):
            selected_value = set(r[0]['Value'] for r in rows if r[2] == 'true')
            if len(selected_value) != 1:
                ok = error('Different values selected for {}'.format(fid))

            # For every set of same features where there is "True" for conflict, at least one should
            # have "True" in the col "Select"
            if not any(r[2] == 'true' for r in rows):
                ok = error('No selected row for {}'.format(fid))

            for row, _, select, cls in rows:
                # For every feature where there is "True" for conflict and nothing for "Select",
                # there should be something in the col "classification of conflict" that comes
                # from this specific list
                if not select:
                    if cls not in classes:
                        ok = error('Invalid classification for {}: {}'.format(fid, cls))

                # Every feature which is True for select should also have "Correct" in
                # "classification of conflict"
                if select == 'true':
                    if cls != 'correct':
                        ok = error('Selected row not classified as correct for {}'.format(fid))

                # Every feature where there is "True" for conflict and "Correct" in
                # "classification of conflict" but nothing in "Select" should have the same Value
                # as whichever row has "Select" =" True in that set of features for that language
                # (this only comes into effect if there is a comparison
                # of more than 2 sheets and one row happens to be better Comment or Source-wise).
                if cls == 'correct' and not select:
                    if row['Value'] not in selected_value:
                        ok = error('Row classified as correct, but value is different from '
                                   'selected value for {}'.format(fid))

            conflicts += 1

    return ok, conflicts


def run(args):
    ok, conflicts = check(args.sheet, args.log)
    if ok:
        args.log.info('{} conflicts'.format(conflicts))
    else:
        args.log.warning('There were errors in the {} conflicts'.format(conflicts))
