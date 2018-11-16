import pytest

from pygrambank import bib


@pytest.mark.parametrize('string, expected', [
    ('h:MacIntirePostman:stuff', ['MacIntire', 'Postman']),
    ('Meier2018', ['Meier']),
])
def test_iter_authors(string, expected):
    assert list(bib.iter_authors(string)) == expected


@pytest.mark.parametrize('string, expected', [
    (
        'Thomas von Mueller',
        [{'firstname': 'Thomas', 'lastname': 'von Mueller'}]),
    (
        'Thomas Mueller',
        [{'firstname': 'Thomas', 'lastname': 'Mueller'}]),
    (
        'T. Mueller and H. Meier',
        [{'firstname': 'T.', 'lastname': 'Mueller'}, {'firstname': 'H.', 'lastname': 'Meier'}]),
    (
        '',
        []),
])
def test_pauthor(string, expected):
    assert bib.pauthor(string) == expected
