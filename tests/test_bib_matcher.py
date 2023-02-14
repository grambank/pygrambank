from pycldf.sources import Source
from pygrambank.cldf import BibliographyMatcher
from pygrambank.sheet import Row


# Make a mock bibliography for testing

FICTIONMAN2000 = dict(
    author='Bob Fictionman',
    year='2000',
    title='Grammar of Martian')

FICTIONMAN2001 = dict(
    author='Fictionman, Bob',
    year='2001',
    title='There are days when my last name comes first')

SPACEMAN1961 = dict(
    author='Space Man, Yuriy',
    year='1961',
    title='Reflections of a man with a space in his name')

WRITEALOT2012_FIRST = dict(
    author='Steve Writealot',
    year='2012',
    title='The first thing I wrote this week')

WRITEALOT2012_ANOTHER = dict(
    author='Steve Writealot',
    year='2012',
    title='Another thing I wrote this week')

STRAUSS_MELPA = dict(
    author='Strauß, Hermann',
    title='Grammatik der Melpa Sprache',
    pages='94',
    year='no date',
    glottolog_ref_id='23344',
    hhtype='grammar_sketch',
    howpublished='Unpublished Manuscript',
    inlg='German [deu]',
    lgcode='Melpa [med]',
    macro_area='Papua')

HINZKUNZ2023 = dict(
    author='Karl Hinz and Karsten Kunz',
    year='2023',
    title="Being cited the 'alternative' way")

BIBLIOGRAPHY = {
    'Fictionman2000': ('book', FICTIONMAN2000),
    'Fictionman2001': ('book', FICTIONMAN2001),
    'Writealot2012_First': ('book', WRITEALOT2012_FIRST),
    'Writealot2012_Another': ('book', WRITEALOT2012_ANOTHER),
    'SpaceMan1961': ('book', SPACEMAN1961),
    's:Strauss:Melpa': ('misc', STRAUSS_MELPA),
    'HinzKunz2023': ('book', HINZKUNZ2023),
}

ENGLISH = 'stan1293'
BIBKEYS_BY_GLOTTOCODE = {
    ENGLISH: {
        'Fictionman2000', 'Fictionman2001', 'HinzKunz2023',
        'SpaceMan1961', 'Writealot2012_First', 'Writealot2012_Another',
    },
    'melp1238': {'s:Strauss:Melpa'},
}


def test_ignore_bare_page_numbers():
    bib_matcher = BibliographyMatcher()
    row = Row(None, None, '1234')
    bib_matcher.add_resolved_citation_to_row(
        ENGLISH, row, BIBLIOGRAPHY, BIBKEYS_BY_GLOTTOCODE)
    assert not bib_matcher.has_sources()
    assert not bib_matcher.has_unresolved_citations()


def test_ignore_personal_comm():
    bib_matcher = BibliographyMatcher()
    row = Row(None, None, 'Müller (p.c.)')
    bib_matcher.add_resolved_citation_to_row(
        ENGLISH, row, BIBLIOGRAPHY, BIBKEYS_BY_GLOTTOCODE)
    assert not bib_matcher.has_sources()
    assert not bib_matcher.has_unresolved_citations()


def test_ignore_empty_source():
    bib_matcher = BibliographyMatcher()
    row = Row(None, None, '')
    bib_matcher.add_resolved_citation_to_row(
        ENGLISH, row, BIBLIOGRAPHY, BIBKEYS_BY_GLOTTOCODE)
    assert not bib_matcher.has_sources()
    assert not bib_matcher.has_unresolved_citations()


def test_report_unresolved_sources():
    bib_matcher = BibliographyMatcher()
    row = Row(None, None, 'Santa Clause (1982)')
    bib_matcher.add_resolved_citation_to_row(
        ENGLISH, row, BIBLIOGRAPHY, BIBKEYS_BY_GLOTTOCODE)
    assert not bib_matcher.has_sources()
    assert bib_matcher.has_unresolved_citations()
    unresolved = bib_matcher.get_unresolved_citations()
    expected_errors = [(('Santa Clause', '1982', ENGLISH), 1)]
    assert unresolved == expected_errors
    assert 'source not confirmed' in row.Source_comment


def test_report_things_that_arent_even_citations():
    bib_matcher = BibliographyMatcher()
    row = Row(None, None, r'¯\_(ツ)_/¯')
    bib_matcher.add_resolved_citation_to_row(
        ENGLISH, row, BIBLIOGRAPHY, BIBKEYS_BY_GLOTTOCODE)
    assert bib_matcher.has_unresolved_citations()
    assert not bib_matcher.has_sources()
    unresolved = bib_matcher.get_unresolved_citations()
    expected_errors = [((r'¯\_(ツ)_/¯', ENGLISH), 1)]
    assert unresolved == expected_errors


def test_report_resolved_source():
    bib_matcher = BibliographyMatcher()
    row = Row(None, None, 'Fictionman (2000)')
    bib_matcher.add_resolved_citation_to_row(
        ENGLISH, row, BIBLIOGRAPHY, BIBKEYS_BY_GLOTTOCODE)
    assert not bib_matcher.has_unresolved_citations()
    assert bib_matcher.has_sources()
    first_source = bib_matcher.get_sources()[0]
    expected_source = Source(
        'book', 'Fictionman2000',
        author='Bob Fictionman',
        year='2000',
        title='Grammar of Martian')
    assert first_source == (expected_source, 1)
    assert row.Source == ['Fictionman2000']


def test_last_name_before_first_name_in_bibliography():
    bib_matcher = BibliographyMatcher()
    row = Row(None, None, 'Fictionman (2001)')
    bib_matcher.add_resolved_citation_to_row(
        ENGLISH, row, BIBLIOGRAPHY, BIBKEYS_BY_GLOTTOCODE)
    assert not bib_matcher.has_unresolved_citations()
    assert bib_matcher.has_sources()
    first_source = bib_matcher.get_sources()[0]
    expected_source = Source(
        'book', 'Fictionman2001',
        author='Fictionman, Bob',
        year='2001',
        title='There are days when my last name comes first')
    assert first_source == (expected_source, 1)
    assert row.Source == ['Fictionman2001']


def test_desambiguate_based_on_title():
    bib_matcher = BibliographyMatcher()
    row = Row(None, None, 'Writealot_another (2012)')
    bib_matcher.add_resolved_citation_to_row(
        ENGLISH, row, BIBLIOGRAPHY, BIBKEYS_BY_GLOTTOCODE)
    assert not bib_matcher.has_unresolved_citations()
    assert bib_matcher.has_sources()
    first_source = bib_matcher.get_sources()[0]
    expected_source = Source(
        'book', 'Writealot2012_Another',
        author='Steve Writealot',
        year='2012',
        title='Another thing I wrote this week')
    assert first_source == (expected_source, 1)
    assert row.Source == ['Writealot2012_Another']


def test_deal_with_people_who_have_spaces_in_their_last_name():
    bib_matcher = BibliographyMatcher()
    row = Row(None, None, 'Space Man (1961)')
    bib_matcher.add_resolved_citation_to_row(
        ENGLISH, row, BIBLIOGRAPHY, BIBKEYS_BY_GLOTTOCODE)
    assert not bib_matcher.has_unresolved_citations()
    assert bib_matcher.has_sources()
    first_source = bib_matcher.get_sources()[0]
    expected_source = Source(
        'book', 'Writealot2012_Another',
        author='Space Man, Yuriy',
        year='1961',
        title='Reflections of a man with a space in his name')
    assert first_source == (expected_source, 1)
    assert row.Source == ['SpaceMan1961']


def test_alternate_citation_style():
    bib_matcher = BibliographyMatcher()
    row = Row(None, None, 'Hinz&Kunz2023, p.113')
    bib_matcher.add_resolved_citation_to_row(
        ENGLISH, row, BIBLIOGRAPHY, BIBKEYS_BY_GLOTTOCODE)
    assert not bib_matcher.has_unresolved_citations()
    assert bib_matcher.has_sources()
    first_source = bib_matcher.get_sources()[0]
    expected_source = Source(
        'book', 'HinzKunz2023',
        author='Karl Hinz and Karsten Kunz',
        year='2023',
        title="Being cited the 'alternative' way")
    assert first_source == (expected_source, 1)
    assert row.Source == ['HinzKunz2023[113]']


def test_hardcoded_fallback():
    bib_matcher = BibliographyMatcher()
    row = Row(None, None, 'Strauß (n.d.)')
    bib_matcher.add_resolved_citation_to_row(
        'melp1238', row, BIBLIOGRAPHY, BIBKEYS_BY_GLOTTOCODE)
    assert not bib_matcher.has_unresolved_citations()
    assert bib_matcher.has_sources()
    first_source = bib_matcher.get_sources()[0]
    expected_source = Source(
        'misc', 's_Strauss_Melpa',
        author='Strauß, Hermann',
        title='Grammatik der Melpa Sprache',
        pages='94',
        year='no date',
        glottolog_ref_id='23344',
        hhtype='grammar_sketch',
        howpublished='Unpublished Manuscript',
        inlg='German [deu]',
        lgcode='Melpa [med]',
        macro_area='Papua')
    assert first_source == (expected_source, 1)
    assert row.Source == ['s_Strauss_Melpa']


def test_nothing_but_von_parts():
    bib_matcher = BibliographyMatcher()
    row = Row(None, None, 'Van der von van 2012')
    bib_matcher.add_resolved_citation_to_row(
        ENGLISH, row, BIBLIOGRAPHY, BIBKEYS_BY_GLOTTOCODE)
    assert bib_matcher.has_unresolved_citations()
    assert not bib_matcher.has_sources()
    unresolved = bib_matcher.get_unresolved_citations()
    expected_errors = [(('Van der von van', '2012', ENGLISH), 1)]
    assert unresolved == expected_errors
