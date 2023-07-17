
def test_api_contributors(api):
    assert api.contributors[0].photo == 'abc'
    assert len(api.contributors[0].roles) == 2


def test_features(api, wiki):
    assert len(api.features) == 10
    assert len(api.features['GB021'].domain) == 2
    f = api.features['GB021']
    assert f.description
    assert f.name
    assert f.patrons
    assert f.id
    assert 'Documentation' in api.features['GB020'].description


def test_bib(api):
    assert len(api.bib) == 6


def test_sheets(api):
    assert len(list(api.iter_sheets())) == 2
