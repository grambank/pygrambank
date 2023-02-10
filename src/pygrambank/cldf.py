import collections
from itertools import groupby
import re

from termcolor import colored

import pyglottolog
from clldutils.misc import lazyproperty, slug
from pycldf.sources import Source

from pygrambank import bib
from pygrambank.srctok import iter_authoryearpages


REGEX_ONLY_PAGES = re.compile(r"[\d+;\s\-etseqpassim.]+$")

MANUAL_SOURCE_MATCHES = {
    ('Strauß', 'n.d.', 'melp1238'): 's:Strauss:Melpa',
    ('Thurston', '1987', 'kuan1248'): 'hvw:Thurston:NBritain',
    ("Z'Graggen", '1969', 'geda1237'): 'hvld:Zgraggen:Madang',
    ('LeCoeur and LeCoeur', '1956', 'daza1242'): 's:LeCoeurLeCoeur:Teda-Daza',
    ('Lindsey', '2018', 'agob1244'): 'Lindsey2018',
    ('Lee', '2005a', 'mada1285'): 'Lee2005a',
    ('Lee', '2005b', 'mada1285'): 'Lee2005b',
}

VON_PREFIXES = ["De", "Da", "Van", "Von", "Van den", "Van der", "Von der", "El", "De la", "De", "d'"]


def undiacritic(s):
    return slug(s, lowercase=False, remove_whitespace=False)


def clean_bibkey(key):
    """Remove colons in bibliography key."""
    # XXX: why?
    return key.replace(':', '_').replace("'", "")


def mismatch_is_fatal(source_string):
    """Filter for source strings."""
    # This code could be combined into one big boolean expression
    # but I somehow doubt that will it any more readable...
    if REGEX_ONLY_PAGES.match(source_string):
        # TODO: Maybe find a way to warn about this
        # print(
        #     'PAGEONLY:',
        #     '[%s] default source:%s' % (glottocode, source_string),
        #     glottocode)
        return False
    elif (
        source_string.find('p.c') != -1
        or source_string.find('personal communication') != -1
        or source_string.find('pers comm') != -1
        or source_string.find('pers. comm') != -1
        or source_string.find('ieldnotes') != -1
        or source_string.find('ield notes') != -1
        or source_string.find('forth') != -1
        or source_string.find('Forth') != -1
        or source_string.find('ubmitted') != -1
        or source_string.find('o appear') != -1
        or source_string.find('in press') != -1
        or source_string.find('in prep') != -1
        or source_string.find('in prog') != -1
        or source_string.startswith('http')
    ):
        return False
    else:
        return True


def _bibkeys_from_citation(
    author, year, pages, word_from_title,
    bibliography_entries, language_bibkeys
):
    citation_lastname = undiacritic(bib.parse_authors(author)[0]['lastname'])
    for name_part in re.split(r'[\s,.\-]+', citation_lastname):
        if name_part.strip() and name_part[0].isupper() and name_part not in VON_PREFIXES:
            citation_firsttoken = name_part
            break
    else:
        citation_firsttoken = None
    word_from_title_norm = word_from_title.replace('_', ' ')

    bibkeys = []
    for bibkey in language_bibkeys:
        bibentry = bibliography_entries[bibkey][1]
        bibtitle = bibentry.get('title', '').lower()
        bibauthors = bibentry.get('author') or bibentry.get('editor') or ''
        family_names = {
            undiacritic(x['lastname'])
            for x in bib.parse_authors(bibauthors)}
        family_names.update(bib.bibkey_authors(bibkey))

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


def _prioritised_bibkeys(bibkeys, bibliography_entries):
    bibkey_rankings = {}
    for bibkey in bibkeys:
        bibentry = bibliography_entries[bibkey][1]
        hhtypes = bib.hhtypes(bibentry)
        hhtype_ranking = max(map(bib.hhtype_priority, hhtypes))
        written_in_english = bib.lgcodestr(bibentry.get('inlg', "")) == ['eng']
        bibkey_rankings[bibkey] = hhtype_ranking, written_in_english
    highest_rank, _ = max(
        (ranking, bibkey)
        for bibkey, ranking in bibkey_rankings.items())
    prioritised_bibkeys = {
        bibkey
        for bibkey, ranking in bibkey_rankings.items()
        if ranking == highest_rank}
    return prioritised_bibkeys


class BibliographyMatcher:

    def __init__(self):
        self._unresolved_citations = collections.Counter()
        self._sources = collections.OrderedDict()

    def has_sources(self):
        """Return True iff. there are citations which could be resolved."""
        return bool(self._sources)

    def get_sources(self):
        """Return a list of resolved sources."""
        return list(self._sources.values())

    def has_unresolved_citations(self):
        """Return True iff. there are citations which couldn't be resolved."""
        return bool(self._unresolved_citations)

    def get_unresolved_citations(self):
        """Return a tuple (citation, count)."""
        return self._unresolved_citations.most_common()

    # XXX this is called by the cldfbench
    def add_resolved_citation_to_row(
        self, glottocode, sheet_row, bibliography_entries, bibkeys_by_glottocode
    ):
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
        authoryears = list(iter_authoryearpages(source_string))
        if not authoryears and mismatch_is_fatal(source_string):
            unmatched_refs.add((source_string, glottocode))

        for author, year, pages, word_from_title in authoryears:
            bibkeys = _bibkeys_from_citation(
                author, year, pages, word_from_title,
                bibliography_entries, bibkeys_by_glottocode.get(glottocode, ()))
            if bibkeys:
                # FIXME: only yield at most one match!?
                matched_refs.update(
                    (bibkey, pages)
                    for bibkey in _prioritised_bibkeys(
                        bibkeys, bibliography_entries))
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
                type_, fields = bibliography_entries[old_bibkey]
                self._sources[new_bibkey] = Source(type_, new_bibkey, **fields)

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
        if not unmatched_refs:
            sheet_row.Source_comment = sheet_row.Source
        else:
            sheet_row.Source_comment = '{} (source not confirmed)'.format(
                sheet_row.Source)


# XXX this is called by the cldfbench
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
