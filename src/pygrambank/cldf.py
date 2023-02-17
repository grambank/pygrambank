import collections
from itertools import groupby
import re
import unicodedata

import pyglottolog
from clldutils.misc import lazyproperty
from pycldf.sources import Source

from pygrambank import bib


MANUAL_SOURCE_MATCHES = {
    ('Strauß', 'n.d.', 'melp1238'): 's:Strauss:Melpa',
    ('Thurston', '1987', 'kuan1248'): 'hvw:Thurston:NBritain',
    ("Z'Graggen", '1969', 'geda1237'): 'hvld:Zgraggen:Madang',
    ('LeCoeur and LeCoeur', '1956', 'daza1242'): 's:LeCoeurLeCoeur:Teda-Daza',
    ('Lindsey', '2018', 'agob1244'): 'Lindsey2018',
    ('Lee', '2005a', 'mada1285'): 'Lee2005a',
    ('Lee', '2005b', 'mada1285'): 'Lee2005b',
}

VON_PREFIXES = [
    'De', 'Da', 'Van', 'Von', 'Van den', 'Van der', 'Von der', 'El', 'De la',
    'De', "d'"]


def undiacritic(s):
    return ''.join(
        ' ' if c.isspace() else c
        for c in unicodedata.normalize('NFD', s)
        if c.isascii() and (c.isalnum() or c.isspace()))


def clean_bibkey(key):
    """Remove colons in bibliography key."""
    return key.replace(':', '_').replace("'", "")


class BibliographyMatcher:
    """Object for resolving citations in a datasheet.

    How to use it:

     1. Loop over the rows of a `Sheet` object.
     2. Call `add_resolved_citation_to_row` on each row.  This part is very
        side-effect-heavy:
        1. The method replaces the Source string in the row with the key of
           the bibliography entry and adds the original citation to the
           `Source_comment` field.  The row is mutated in-place.
        2. The object keeps an record of any matched sources.
        3. The object also keeps a record for all citations that failed to
           match.
     3. Get matched sources via the `get_sources()` method.
     4. For error handling, get all failed matches via the
        `get_unresolved_citations()` method.
    """

    def __init__(self, bibliography_entries, bibkeys_by_glottocode):
        self._unresolved_citations = collections.Counter()
        self._sources = collections.OrderedDict()
        self._source_occurrences = collections.Counter()
        self._bibliography_entries = bibliography_entries
        self._bibkeys_by_glottocode = bibkeys_by_glottocode

        # Note: Caching the family names of the authors because parsing them
        # turned out to be quite expensive.
        self._parsed_author_cache = {}

    def has_sources(self):
        """Return True iff. there are citations which could be resolved."""
        return bool(self._sources)

    def get_sources(self):
        """Return a list of tuples (source, occurrence_count)."""
        return [
            (source, self._source_occurrences[bibkey])
            for bibkey, source in self._sources.items()]

    def has_unresolved_citations(self):
        """Return True iff. there are citations which couldn't be resolved."""
        return bool(self._unresolved_citations)

    def get_unresolved_citations(self):
        """Return a list of tuples (citation, occurrence_count)."""
        return self._unresolved_citations.most_common()

    def _parse_authors(self, bibkey):
        """Return set of family names of authors for a bibkey (cached)."""
        if bibkey in self._parsed_author_cache:
            return self._parsed_author_cache[bibkey]
        else:
            bibentry = self._bibliography_entries[bibkey][1]
            bibauthors = bibentry.get('author') or bibentry.get('editor') or ''
            family_names = {
                undiacritic(x['lastname'])
                for x in bib.parse_authors(bibauthors)}
            family_names.update(bib.bibkey_authors(bibkey))
            self._parsed_author_cache[bibkey] = family_names
            return family_names

    def _bibkeys_from_citation(
        self, author, year, pages, word_from_title, glottocode
    ):
        """Return bibliography keys corresponding to a citation."""

        citation_lastname = undiacritic(bib.parse_authors(author)[0]['lastname'])
        for name_part in re.split(r'[\s,.\-]+', citation_lastname):
            if name_part.strip() and name_part[0].isupper() and name_part not in VON_PREFIXES:
                citation_firsttoken = name_part
                break
        else:
            citation_firsttoken = None
        word_from_title_norm = word_from_title.replace('_', ' ')

        bibkeys = []
        for bibkey in self._bibkeys_by_glottocode[glottocode]:
            bibentry = self._bibliography_entries[bibkey][1]
            bibtitle = bibentry.get('title', '').lower()
            family_names = self._parse_authors(bibkey)

            if year not in bibentry.get('year', ''):
                continue
            if word_from_title_norm and word_from_title_norm not in bibtitle:
                continue
            if not any(
                citation_firsttoken in re.split(r'[\s,.\-]+', lastname)
                for lastname in family_names
            ):
                continue

            bibkeys.append(bibkey)

        return bibkeys

    def add_resolved_citation_to_row(self, glottocode, sheet_row):
        """Destructively add citations to the row of a datasheet.

        The `BibliographyMatcher` keeps track of all matched or unmatched
        citations it encounters.  Those can be retrieved using the
        `get_sources` and `get_unresolved_citations` methods.
        """
        if not sheet_row.Source:
            return

        matched_refs = set()
        unmatched_refs = set()

        source_string = sheet_row.Source
        authoryears = list(bib.iter_authoryearpages(source_string))
        if not authoryears and bib.mismatch_is_fatal(source_string):
            unmatched_refs.add((source_string, glottocode))

        for author, year, pages, word_from_title in authoryears:
            bibkeys = self._bibkeys_from_citation(
                author, year, pages, word_from_title, glottocode)
            if bibkeys:
                # FIXME: only yield at most one match!?
                matched_refs.update(
                    (bibkey, pages)
                    for bibkey in bib.prioritised_bibkeys(
                        bibkeys, self._bibliography_entries))
            elif (author, year, glottocode) in MANUAL_SOURCE_MATCHES:
                matched_refs.add(
                    (MANUAL_SOURCE_MATCHES[(author, year, glottocode)], pages))
            else:
                unmatched_refs.add((author, year, glottocode))

        # output: record unsucessful matches

        self._unresolved_citations.update(unmatched_refs)

        # output: record successful matches

        matched_refs = sorted(matched_refs, key=lambda r: (r[0], r[1] or ''))
        matched_refs = [
            (key, clean_bibkey(key), pages) for key, pages in matched_refs]

        for old_bibkey, new_bibkey, _ in matched_refs:
            if new_bibkey not in self._sources:
                type_, fields = self._bibliography_entries[old_bibkey]
                self._sources[new_bibkey] = Source(type_, new_bibkey, **fields)
            self._source_occurrences[new_bibkey] += 1

        # output: update sheet row

        pages_for_bibkey = collections.OrderedDict()
        for new_bibkey, key_refs in groupby(matched_refs, lambda ref: ref[1]):
            if new_bibkey not in pages_for_bibkey:
                pages_for_bibkey[new_bibkey] = set()
            pages_for_bibkey[new_bibkey].update(
                pages for _, _, pages in key_refs if pages)

        sheet_row.Source = [
            '{}{}'.format(
                new_bibkey,
                '[{}]'.format(','.join(sorted(pages))) if pages else '')
            for new_bibkey, pages in pages_for_bibkey.items()]
        if not sheet_row.Source and bib.mismatch_is_fatal(source_string):
            sheet_row.Source_comment = '{} (source not confirmed)'.format(
                source_string)
        else:
            sheet_row.Source_comment = source_string


class GlottologGB(object):
    """
    A custom facade to the Glottolog API.
    """
    def __init__(self, repos):
        self.api = repos if isinstance(repos, pyglottolog.Glottolog) \
            else pyglottolog.Glottolog(repos)

    def bib(self, key):
        """
        Retrieve entries of a Glottolog BibTeX file.

        :param key: filename stem of the BibTeX file, e.g. "hh" for "hh.bib"
        :return: dict mapping citation keys to (type, fields) pairs.
        """
        return {
            e.key: (e.type, e.fields)
            for e in self.api.bibfiles['{0}.bib'.format(key)].iterentries()}

    @lazyproperty
    def languoids(self):
        return list(self.api.languoids())

    @lazyproperty
    def languoids_by_glottocode(self):
        return {lang.id: lang for lang in self.languoids}

    @lazyproperty
    def descendants_map(self):
        res = collections.defaultdict(list)
        for lang in self.languoids:
            res[lang.id].append(lang.id)
            if lang.lineage:
                for _, gc, _ in lang.lineage:
                    res[gc].append(lang.id)
        return res

    @lazyproperty
    def languoids_by_ids(self):
        """
        We provide a simple lookup for the three types of identifiers for a Glottolog languoid,
        where hid takes precedence over ISO 639-3 code.
        """
        res = {}
        for lang in self.languoids:
            res[lang.id] = lang
            if lang.iso:
                res[lang.iso] = lang
        for lang in self.languoids:
            if lang.hid:
                res[lang.hid] = lang
        return res
