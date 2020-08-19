import pytest

from pygrambank import sheet


@pytest.fixture
def sheet_abbr(api):
    return sheet.Sheet(api.sheets_dir / 'ABBR_abcd1234.tsv')


def test_visitor(sheet_abbr):
    class Counter(object):
        def __init__(self):
            self.c = 0

        def __call__(self, *args, **kw):
            self.c += 1

    c = Counter()
    sheet_abbr.visit(c)
    assert c.c == 2


def test_check(api, sheet_abbr):
    assert sheet_abbr.check(api) >\
           sheet.Sheet(api.sheets_dir / 'NOVALS_abcd1234.tsv').check(api)


def test_values(sheet_abbr, api):
    assert len(list(sheet_abbr.iter_row_objects(api))) == 1