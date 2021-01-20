"""

"""
import pathlib

from csvw.dsv import reader


def register(parser):  # pragma: no cover
    parser.add_argument('groupings')


def run(args):  # pragma: no cover
    for p in pathlib.Path(args.groupings).glob('*.csv'):
        groupings = {r['Feature_ID']: r for r in reader(p, dicts=True)}
        new_features = []
        for feature in args.repos.ordered_features:
            for k, v in groupings[feature.id].items():
                if k != 'Feature_ID':
                    if k in feature:
                        pass
                    else:
                        feature[k] = v
            new_features.append(feature)
    args.repos.gb20.save(new_features)
