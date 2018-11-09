
def test_features(api):
    assert len(api.features) == 9
    assert len(api.features['GB020'].domain) == 2
    f = api.features['GB020']
    assert f.description
    assert f.name
    assert f.patron
    assert f.id


def test_bib(api):
    assert len(api.bib) == 1


def test_sheets(api):
    assert len(list(api.sheets_dir.glob('*.csv'))) == 1
