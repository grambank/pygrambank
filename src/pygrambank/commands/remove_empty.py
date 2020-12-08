"""
Removes empty columns and rows from a tsv file.
"""
from csvw import dsv
from clldutils.clilib import PathType
from pygrambank.sheet import Sheet


def register(parser):
    parser.add_argument('path', nargs='+', type=PathType(type='file'))


def run(args):
    for p in args.path:
        # use reader rather than iterrows so we operate on raw file rather than a
        # grambank-ifyed version.
        rows = list(Sheet(p)._reader())
        not_empty = None
        with dsv.UnicodeWriter(p, delimiter='\t', encoding='utf8') as w:
            for i, row in enumerate(rows):
                if i == 0:
                    not_empty = [i for i, k in enumerate(row) if k]
                if set(row) == {''}:
                    continue
                # check other cells are empty
                for i, e in enumerate(row):
                    if i not in not_empty and e:  # pragma: no cover
                        raise ValueError(
                            "Unlabelled column has value on line %d. Fix manually!" % i
                        )
                w.writerow([row[i] for i in not_empty])
    return
