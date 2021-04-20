import pathlib

import pytest

from pygrambank.cldf import Glottolog
from pygrambank import sheet


@pytest.fixture
def sheet_abbr(api):
    return sheet.Sheet(api.sheets_dir / 'ABBR_abcd1234.tsv')


@pytest.fixture
def sheet_factory(tmp_path):
    def _make_one(text, name='ABBR_bcde1234.tsv'):
        fname = tmp_path / name
        fname.write_text(text, encoding='utf8')
        return sheet.Sheet(fname)
    return _make_one


def test_visitor(sheet_abbr):
    class Counter(object):
        def __init__(self):
            self.c = 0

        def __call__(self, *args, **kw):
            self.c += 1

    c = Counter()
    sheet_abbr.visit(c)
    assert c.c == 2


def test_check(api, sheet_abbr, sheet_factory, capsys):
    assert sheet_abbr.check(api) >\
           sheet.Sheet(api.sheets_dir / 'NOVALS_abcd1234.tsv').check(api)


@pytest.mark.filterwarnings("ignore:Duplicate")
@pytest.mark.parametrize(
    'text,error',
    [
        ('Value', 'missing column'),
        ('Value\tValue', 'duplicate header'),
        ('Feature_ID\tValue\tSource\tComment\t\nGB020\t1\t\t\tx', 'non-empty cell'),
        ('Feature_ID\tValue\tSource\tComment\t\nGB020\t1\t\t\tx\nGB020\t0\t\t\t', 'inconsistent'),
    ]
)
def test_check2(api, sheet_factory, text, error, capsys):
    s = sheet_factory(text)
    s.check(api)
    out, _ = capsys.readouterr()
    assert error in out


def test_values(sheet_abbr, api):
    assert len(list(sheet_abbr.iter_row_objects(api))) == 1


def test_Sheet(api, capsys, sheet_factory):
    s = sheet_factory("""Feature_ID\tValue\tSource\tComment\tContributed datapoints
GB020\t0\tMeier 2007\t\tHJH\n""")
    assert str(s).endswith('tsv')
    rows = list(s.iter_row_objects(api))
    assert rows[0].sources[0].key == ('Meier', '2007', None)
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
