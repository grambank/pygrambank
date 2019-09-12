from pygrambank import sheet


def test_check(api):
    assert sheet.Sheet(api.sheets_dir / 'ABBR_abcd1234.tsv').check(api) >\
           sheet.Sheet(api.sheets_dir / 'NOVALS_abcd1234.tsv').check(api)
