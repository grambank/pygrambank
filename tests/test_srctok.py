from collections import Counter, defaultdict

import pytest

from pygrambank import bib
from pygrambank.srctok import source_to_refs, allmax, matchauthor


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
    res = source_to_refs('Meier 2007', 'x', {}, {}, Counter(), {('Meier', '2007', 'x'): 'abc'})
    assert res[0][0][0] == 'abc'


def test_source_to_refs_multi_word_name(bibs_and_lgks):
    bibs, lgks = bibs_and_lgks
    assert source_to_refs('Last Name 2000', 'abc', bibs, lgks, Counter())[0] == [('multi_word_name_1', [])]
    assert source_to_refs('Last Name 1900', 'abc', bibs, lgks, Counter())[0] == [('multi_word_name_2', [])]


def test_source_to_refs_disambiguation_by_title(bibs_and_lgks):
    bibs, lgks = bibs_and_lgks
    assert source_to_refs('Author_beta 2020', 'abc', bibs, lgks, {})[0] == [('book2020b', [])]
    assert source_to_refs('Author_alpha 2020', 'abc', bibs, lgks, {})[0] == [('book2020a', [])]
    unresolved = Counter()
    assert source_to_refs('Author nd', 'abc', bibs, lgks, unresolved)[0] == [('bookc', [])]


def test_misc():
    assert allmax({}) == {}


def test_matchauthor():
    assert not matchauthor('Hans Meier', '', [])
    assert matchauthor('Hans Meier', 'Hans Meier', [])
