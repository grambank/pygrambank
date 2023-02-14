from pygrambank import bib


def test_author_extraction_from_bibkeys():
    assert list(bib.bibkey_authors('h:MacIntirePostman:stuff')) == ['MacIntire', 'Postman']
    assert list(bib.bibkey_authors('Meier2018')) == ['Meier']


def test_empty_author_string_yields_no_authors():
    author_string = ''
    authors = []
    assert list(bib.parse_authors(author_string)) == authors


def test_simple_first_name_plus_last_name():
    author_string = 'Thomas Mueller'
    authors = [{'firstname': 'Thomas', 'lastname': 'Mueller'}]
    assert list(bib.parse_authors(author_string)) == authors


def test_simple_last_name_plus_first_name():
    author_string = 'Mueller, Thomas'
    authors = [{'firstname': 'Thomas', 'lastname': 'Mueller'}]
    assert list(bib.parse_authors(author_string)) == authors


def test_multiple_authors():
    author_string = 'T. Mueller and H. Meier'
    authors = [
        {'firstname': 'T.', 'lastname': 'Mueller'},
        {'firstname': 'H.', 'lastname': 'Meier'},
    ]
    assert list(bib.parse_authors(author_string)) == authors


def test_von_part():
    author_string = 'Carl-Friedrich von Adelswegen'
    authors = [{'firstname': 'Carl-Friedrich', 'lastname': 'von Adelswegen'}]
    assert list(bib.parse_authors(author_string)) == authors

    author_string = 'von Adelswegen, Carl-Friedrich'
    authors = [{'firstname': 'Carl-Friedrich', 'lastname': 'von Adelswegen'}]
    assert list(bib.parse_authors(author_string)) == authors

    author_string = 'Adelswegen, Jr., Carl-Friedrich von'
    # is that really intended behaviour...?
    authors = [{
        'firstname': 'Carl-Friedrich von',
        'lastname': 'Adelswegen',
        'jr': 'Jr.'
    }]
    assert list(bib.parse_authors(author_string)) == authors
