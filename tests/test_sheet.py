import pathlib
import unittest

import pytest

from pygrambank.cldf import GlottologGB
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


class FeatureDependencies(unittest.TestCase):

    def row(self, feature_id, value, comment=None):
        return sheet.Row(
            Feature_ID=feature_id,
            Value=value,
            Source='',
            Comment=comment or '')

    def test_gb408_to_410(self):
        good_rows = [
            self.row('GB408', '0'),
            self.row('GB409', '0'),
            self.row('GB410', '1')]
        bad_rows = [
            self.row('GB408', '0'),
            self.row('GB409', '0'),
            self.row('GB410', '0')]
        self.assertEqual(len(sheet.check_feature_dependencies(good_rows)), 0)
        self.assertEqual(len(sheet.check_feature_dependencies(bad_rows)), 1)

    def test_gb131_to_133(self):
        good_rows = [
            self.row('GB131', '0'),
            self.row('GB132', '0'),
            self.row('GB133', '1')]
        bad_rows = [
            self.row('GB131', '0'),
            self.row('GB132', '0'),
            self.row('GB133', '0')]
        self.assertEqual(len(sheet.check_feature_dependencies(good_rows)), 0)
        self.assertEqual(len(sheet.check_feature_dependencies(bad_rows)), 1)

    def test_gb309(self):
        good_rows = [
            self.row('GB083', '0'),
            self.row('GB084', '0'),
            self.row('GB121', '0'),
            self.row('GB521', '1'),
            self.row('GB309', '1')]
        bad_rows = [
            self.row('GB083', '0'),
            self.row('GB084', '0'),
            self.row('GB121', '0'),
            self.row('GB521', '0'),
            self.row('GB309', '1')]
        fixed_rows = [
            self.row('GB083', '0'),
            self.row('GB084', '0'),
            self.row('GB121', '0'),
            self.row('GB521', '0'),
            self.row('GB309', '1', 'comment')]
        self.assertEqual(len(sheet.check_feature_dependencies(good_rows)), 0)
        self.assertEqual(len(sheet.check_feature_dependencies(bad_rows)), 1)
        self.assertEqual(len(sheet.check_feature_dependencies(fixed_rows)), 0)

    def test_gb333_to_336(self):
        good_rows = [
            self.row('GB333', '1'),
            self.row('GB334', '0'),
            self.row('GB335', '0'),
            self.row('GB336', '0')]
        bad_rows = [
            self.row('GB333', '0'),
            self.row('GB334', '0'),
            self.row('GB335', '0'),
            self.row('GB336', '0')]
        fixed_rows = [
            self.row('GB333', '0', 'comment'),
            self.row('GB334', '0', 'comment'),
            self.row('GB335', '0', 'comment'),
            self.row('GB336', '0', 'comment')]
        self.assertEqual(len(sheet.check_feature_dependencies(good_rows)), 0)
        self.assertEqual(len(sheet.check_feature_dependencies(bad_rows)), 4)
        self.assertEqual(len(sheet.check_feature_dependencies(fixed_rows)), 0)

    def test_comments_in_various_features(self):
        good_rows = [
            self.row('GB026', '0'),
            self.row('GB129', '0'),
            self.row('GB165', '0'),
            self.row('GB166', '0'),
            self.row('GB197', '0'),
            self.row('GB260', '0'),
            self.row('GB285', '0'),
            self.row('GB303', '0'),
            self.row('GB319', '0'),
            self.row('GB320', '0'),
            self.row('GB336', '0')]
        bad_rows = [
            self.row('GB026', '1'),
            self.row('GB129', '1'),
            self.row('GB165', '1'),
            self.row('GB166', '1'),
            self.row('GB197', '1'),
            self.row('GB260', '1'),
            self.row('GB285', '1'),
            self.row('GB303', '1'),
            self.row('GB319', '1'),
            self.row('GB320', '1'),
            self.row('GB336', '1')]
        fixed_rows = [
            self.row('GB026', '1', 'comment'),
            self.row('GB129', '1', 'comment'),
            self.row('GB165', '1', 'comment'),
            self.row('GB166', '1', 'comment'),
            self.row('GB197', '1', 'comment'),
            self.row('GB260', '1', 'comment'),
            self.row('GB285', '1', 'comment'),
            self.row('GB303', '1', 'comment'),
            self.row('GB319', '1', 'comment'),
            self.row('GB320', '1', 'comment'),
            self.row('GB336', '1', 'comment')]
        self.assertEqual(len(sheet.check_feature_dependencies(good_rows)), 0)
        self.assertEqual(len(sheet.check_feature_dependencies(bad_rows)), 11)
        self.assertEqual(len(sheet.check_feature_dependencies(fixed_rows)), 0)

    def test_gb265_266_274(self):
        good_rows = [
            self.row('GB265', '1'),
            self.row('GB266', '0'),
            self.row('GB273', '0')]
        bad_rows = [
            self.row('GB265', '0'),
            self.row('GB266', '0'),
            self.row('GB273', '0')]
        fixed_rows = [
            self.row('GB265', '0', 'comment'),
            self.row('GB266', '0', 'comment'),
            self.row('GB273', '0', 'comment')]
        self.assertEqual(len(sheet.check_feature_dependencies(good_rows)), 0)
        self.assertEqual(len(sheet.check_feature_dependencies(bad_rows)), 3)
        self.assertEqual(len(sheet.check_feature_dependencies(fixed_rows)), 0)

    def test_gb072_to_075(self):
        good_rows = [
            self.row('GB072', '1'),
            self.row('GB073', '0'),
            self.row('GB074', '0'),
            self.row('GB075', '0')]
        bad_rows = [
            self.row('GB072', '0'),
            self.row('GB073', '0'),
            self.row('GB074', '0'),
            self.row('GB075', '0')]
        fixed_rows = [
            self.row('GB072', '0'),
            self.row('GB073', '0'),
            self.row('GB074', '0', 'comment'),
            self.row('GB075', '0', 'comment')]
        self.assertEqual(len(sheet.check_feature_dependencies(good_rows)), 0)
        self.assertEqual(len(sheet.check_feature_dependencies(bad_rows)), 2)
        self.assertEqual(len(sheet.check_feature_dependencies(fixed_rows)), 0)

    def test_gb155_and_133(self):
        good_rows = [
            self.row('GB113', '0'),
            self.row('GB155', '0')]
        bad_rows = [
            self.row('GB113', '0'),
            self.row('GB155', '1')]
        fixed_rows = [
            self.row('GB113', '0', 'comment'),
            self.row('GB155', '1', 'comment')]
        self.assertEqual(len(sheet.check_feature_dependencies(good_rows)), 0)
        self.assertEqual(len(sheet.check_feature_dependencies(bad_rows)), 2)
        self.assertEqual(len(sheet.check_feature_dependencies(fixed_rows)), 0)

    def test_gb022_and_023(self):
        good_rows = [
            self.row('GB022', '0'),
            self.row('GB023', '1')]
        bad_rows = [
            self.row('GB022', '1'),
            self.row('GB023', '1')]
        fixed_rows = [
            self.row('GB022', '1', 'comment'),
            self.row('GB023', '1', 'comment')]
        self.assertEqual(len(sheet.check_feature_dependencies(good_rows)), 0)
        self.assertEqual(len(sheet.check_feature_dependencies(bad_rows)), 2)
        self.assertEqual(len(sheet.check_feature_dependencies(fixed_rows)), 0)


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
    assert rows[0].sources[0].key == ('Meier', '2007', '')
    assert len(rows) == 1
    md = s.metadata(GlottologGB(pathlib.Path(__file__).parent / 'glottolog'))
    out, _ = capsys.readouterr()
    assert 'no macroareas' in out
    assert md['Language_level_ID'] == 'abcd1234'
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
