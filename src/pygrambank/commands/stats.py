"""
Summary stats on the sheets in original_sheets/
"""
import collections


def run(args):
    api = args.repos

    sheets = [s for s in api.iter_sheets()]
    values = collections.Counter()
    cols = collections.Counter()

    print(api)

    print('\nSheets with BOM:')
    for sheet in sorted(sheets, key=lambda s: s.path):
        if sheet.path.read_text(encoding='utf-8').startswith('\ufeff'):
            print(sheet.path)
        for i, val in enumerate(sheet._reader(dicts=True)):
            if i == 0:
                cols.update(list(val.keys()))
            values.update([sheet.path.stem])
    print('\n{} sheets with {} rows'.format(len(values), sum(values.values())))
    print('\nMost common columns:')
    for k, v in cols.most_common(10):
        print(k, v)
