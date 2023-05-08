from pygrambank import features


def test_gb20_update(api):
    def visit(f, api):
        f['xyz'] = 'abcdefg'
        return f

    api.visit_feature(visit)
    new = (api.repos / 'gb20.txt').read_text(encoding='utf-8')
    assert 'xyz' in new
    assert 'abcdefg' in new
