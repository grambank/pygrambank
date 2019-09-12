from pygrambank import sheet


def test_visitor(api):
    class Counter(object):
        def __init__(self):
            self.c = 0

        def __call__(self, *args, **kw):
            self.c += 1

    sh = sheet.Sheet(api.sheets_dir / 'ABBR_abcd1234.tsv')
    c = Counter()
    sh.visit(c)
    assert c.c == 2


def test_check(api):
    assert sheet.Sheet(api.sheets_dir / 'ABBR_abcd1234.tsv').check(api) >\
           sheet.Sheet(api.sheets_dir / 'NOVALS_abcd1234.tsv').check(api)
