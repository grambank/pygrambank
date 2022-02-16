"""

"""
import os
import shutil
import collections


def run(args):
    gcs = collections.Counter(p.stem.split('_')[-1] for p in args.repos.path('original_sheets').glob('*.tsv'))
    for p in args.repos.path('conflicts').glob('*.tsv'):
        if p.stem in gcs:
            if gcs[p.stem] == 1:
                print(p)
                shutil.move(p, args.repos.path('conflicts_resolved', p.name))
                #os.system('grambank check_conflicts {}'.format(p))
                #break