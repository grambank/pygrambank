from collections import Counter, defaultdict

import pytest

from pygrambank import bib
from pygrambank.srctok import source_to_refs


@pytest.fixture
def bibs_and_lgks(api):
    bibs = api.bib
    lgks = defaultdict(set)
    for key, (typ, fields) in bibs.items():
        if 'lgcode' in fields:
            for code in bib.lgcodestr(fields['lgcode']):
                lgks[code].add(key)
    return bibs, lgks


def test_source_to_refs(capsys):
    source_to_refs('1234', 'x', {}, {}, Counter())
    out, _ = capsys.readouterr()
    assert 'PAGEONLY' in out
    assert source_to_refs('p.c.', 'x', {}, {}, Counter())[0] == []
    unresolved = Counter()
    source_to_refs('Meier 2018', 'x', {}, {}, unresolved)
    assert unresolved
    assert not source_to_refs('', 'x', {}, {}, unresolved)[0]
    assert source_to_refs('Gwynn&Krishnamurti1985, p.144', 'x', {}, {}, unresolved)[0] == []


def test_source_to_refs_disambiguation_by_title(bibs_and_lgks):
    bibs, lgks = bibs_and_lgks
    assert source_to_refs('Author_beta 2020', 'abc', bibs, lgks, {})[0] == [('book2020b', [])]
    assert source_to_refs('Author_alpha 2020', 'abc', bibs, lgks, {})[0] == [('book2020a', [])]
    unresolved = Counter()
    assert source_to_refs('Author nd', 'abc', bibs, lgks, unresolved)[0] == [('bookc', [])]
