from clldutils.path import read_text

from pygrambank import features


def test_gb20(api, wiki, capsys):
    gb20 = features.GB20(api.repos / 'gb20.txt')
    api.repos.joinpath('For_coders').mkdir()
    gb20.grambank_sheet()
    gb20.features_sheet()
    gb20.listallwiki(wiki)


def test_gb20_update(api):
    def visit(f, api):
        f['xyz'] = 'abcdefg'
        return f

    api.visit_feature(visit)
    new = read_text(api.repos / 'gb20.txt')
    assert 'xyz' in new
    assert 'abcdefg' in new
