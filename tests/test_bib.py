from pygrambank import bib


def test_author_extraction_from_bibkeys():
    assert list(bib.bibkey_authors('h:MacIntirePostman:stuff')) == ['MacIntire', 'Postman']
    assert list(bib.bibkey_authors('Meier2018')) == ['Meier']


def test_pauthor():
    author_string = ''
    authors = []
    assert list(bib.parse_authors(author_string)) == authors

    author_string = 'Thomas Mueller'
    authors = [{'firstname': 'Thomas', 'lastname': 'Mueller'}]
    assert list(bib.parse_authors(author_string)) == authors

    author_string = 'Mueller, Jr., Hans d\'er von'
    authors = [{
        'jr': 'Jr.',
        'firstname': 'Hans d\'er von',
        'lastname': 'Mueller'}]
    assert list(bib.parse_authors(author_string)) == authors

    author_string = 'Thomas von Mueller'
    authors = [{'firstname': 'Thomas', 'lastname': 'von Mueller'}]
    assert list(bib.parse_authors(author_string)) == authors

    author_string = 'T. Mueller and H. Meier'
    authors = [
        {'firstname': 'T.', 'lastname': 'Mueller'},
        {'firstname': 'H.', 'lastname': 'Meier'}]
    assert list(bib.parse_authors(author_string)) == authors
