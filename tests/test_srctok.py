from collections import Counter

from pygrambank.srctok import source_to_refs


def test_source_to_refs(capsys):
    source_to_refs('1234', 'x', {}, {}, {})
    out, _ = capsys.readouterr()
    assert 'PAGEONLY' in out
    assert source_to_refs('p.c', 'x', {}, {}, {}) == []
    unresolved = Counter()
    source_to_refs('Meier 2018', 'x', {}, {}, unresolved)
    assert unresolved
    assert not source_to_refs('', 'x', {}, {}, unresolved)
