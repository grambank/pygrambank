import pytest

from pygrambank import util


@pytest.mark.parametrize(
    'fname,nrows',
    [
        ('Other Coder_Lang [NOCODE_lang].xlsx', 2),
        ('Some One_Some Lang [NOCODE_xyz].csv', 0),
        ('The Other Coder_Language [iso].tsv', 1),
        ('Yet Another Coder_New Lang [abcd1234].xls', 0),
    ]
)
def test_write_tsv(api, tmp_path, fname, nrows):
    assert nrows == util.write_tsv(
        api.path('obsolete_sheets', fname), tmp_path / 't.tsv', 'abcd1234')
