"""
Applies fixes to sheets imported from the HG project. Rows to fix are identified by
- matching (Feature_ID, Value) against a list of known problems and
- checking whether the original "Autotranslated" comment is still there.
"""
import collections

from csvw.dsv import reader


class Fix:  # pragma: no cover
    def __init__(self, spec):
        self.spec = collections.defaultdict(list)
        for r in reader(spec, dicts=True):
            if r['find']:
                assert ':' in r['find'], r['find']
                self.spec[tuple(r['find'].split(':'))].append(r)

    def __call__(self, row):
        for k, v in row.items():
            if ('ontributed' in k) and ('atapoint' in k):
                if v.strip():
                    return True
        for key in [(row['Feature_ID'], row['Value']), (row['Feature_ID'], '*')]:
            if key in self.spec:
                # We found a matching datapoint ...
                for spec in self.spec[key]:
                    if spec['Mapping'] in row['Comment'] and ('MM' not in row['Comment']):
                        # ... with a matching "Autotranslated" comment.
                        fid, val = spec['replace'].replace('GB86', 'GB086').split(':')
                        assert fid == row['Feature_ID'], spec
                        row['Value'] = val
                        if not val.strip():
                            row['Comment'] = ''
                            row['Source'] = ''
                        break
        return True


def run(args):  # pragma: no cover
    fix = Fix(args.repos.repos / 'HG_import' / 'HG_GB_mapping_JV_HS_revise.csv')
    for sheet in args.repos.iter_sheets():
        if sheet.path.stem.startswith('CB-'):
            sheet.visit(row_visitor=fix)
