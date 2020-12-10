import pathlib

import pytest

from pygrambank.cldf import Glottolog
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


def test_Sheet(tmpdir, api, capsys, mocker):
    fname = pathlib.Path(str(tmpdir)) / 'ABBR_bcde1234.tsv'
    fname.write_text("""Feature_ID\tValue\tSource\tComment\tContributed datapoints
GB020\t0\tThe Book\t\tHJH\n""", encoding='utf8')
    s = sheet.Sheet(fname)
    assert str(s).endswith('tsv')
    rows = list(s.iter_row_objects(api))
    assert len(rows) == 1
    md = s.metadata(Glottolog(pathlib.Path(__file__).parent / 'glottolog'))
    out, _ = capsys.readouterr()
    assert 'no macroareas' in out
    assert md['Language_ID'] == 'abcd1234'
    assert s.visit() == (1, 1)


@pytest.mark.parametrize(
    'row,logs',
    [
        (dict(Feature_ID='XX056', Value='1', Source='Ref'), True),
        (dict(Feature_ID='GB020', Value='x', Source='Ref', Comment=''), True),
        (dict(Feature_ID='GB020', Value='', Source='Ref', Comment=''), True),
        (dict(Feature_ID='GB020', Value='', Source='', Comment='text'), True),
        (dict(Feature_ID='', Value='1', Source='Ref'), False),
    ]
)
def test_valid_row(sheet_abbr, api, mocker, row, logs):
    log = mocker.Mock()
    assert not sheet_abbr.valid_row(row, api, log=log)
    assert (not logs) or log.called
