"""

"""
import itertools

from csvw.dsv import reader


def register(parser):  # pragma: no cover
    parser.add_argument('groupings')


def run(args):  # pragma: no cover
    groupings = {r['ID']: r for r in reader(args.groupings, dicts=True, delimiter='\t')}
    new_features = []
    for feature in args.repos.ordered_features:
        for k, v in itertools.dropwhile(
                lambda i: i[0] != 'bound_morphology', groupings[feature.id].items()):
            feature[k] = v
        new_features.append(feature)
    args.repos.gb20.save(new_features)
