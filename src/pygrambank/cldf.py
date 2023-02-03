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

REFS = {
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


# XXX this is called by the cldfbench
def bibdata(sheet, sheet_rows, bibliography_entries, bibkeys_by_glottocode, unresolved):
    fixrefs = REFS

    glottocode = sheet.glottocode
    language_bibkeys = bibkeys_by_glottocode.get(glottocode, ())

    # XXX: this entire function could just just be called for a single row
    # in the datasheet, e.g.
    # sources = [src
    #            for sheet in sheets
    #            for row in sheet.iter_rows()
    #            for src in bibdata(sheet, row, ...)]
    for row in sheet_rows:
        if not row.Source:
            continue

        # FIXME mutating input data in-place!!!
        row.Source_comment = row.Source

        source_string = row.Source
        authoryears = list(iter_authoryearpages(source_string))

        ### XXX: THIS IS THE CODE THAT MATCHES SOURCES ###

        matched_refs = set()
        # XXX: what's the difference between unmatched and unresolved refs
        # A: oh, I guess `unmatched_refs` is just there to make sure that
        # there's only one PARTIAL FAIL message per author_year_tuple.
        unmatched_refs = set()
        unresolved_sources = []

        for author_year_tuple in authoryears:
            author, year, pages, word_from_title = author_year_tuple
            citation_lastname = undiacritic(bib.parse_authors(author)[0]['lastname'])
            citation_firsttoken = None
            for name_part in re.split(r'[\s,.\-]+', citation_lastname):
                if name_part.strip() and name_part[0].isupper() and name_part not in VON_PREFIXES:
                    citation_firsttoken = name_part
                    break
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

            if bibkeys:

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
                for bibkey in prioritised_bibkeys:
                    # FIXME: only yield at most one match!?
                    matched_refs.add((bibkey, pages))

            elif author_year_tuple not in unmatched_refs:

                # TODO: just do the printing at the end of the loop...
                print(colored('PARTIAL FAIL', color='red'))
                print('WARNING: unmatched reference: {}'.format(author_year_tuple))
                unmatched_refs.add(author_year_tuple)

        matched_refs = sorted(matched_refs, key=lambda r: (r[0], r[1] or ''))

        ### XXX: THIS IS THE CODE THAT HANDLES MATCH FAILURES ###
        # (I guess this is where the PARTIAL FAIL messages should be printed?)

        src_comment = None
        if not matched_refs:
            # XXX: those are the fallback options when matching fails:
            #  * complain about bare page numbers
            #  * just ignore all the Lehmann-(p.c.)-like citations
            #  * fill in fallbacks from FIXREFS
            #    ^ XXX: maybe do the FIXREFS thing first and turn the rest of
            #    this entire block into 'complain and move on' code?
            #  * record missing match in `unresolved`

            if REGEX_ONLY_PAGES.match(source_string):
                print(
                    'PAGEONLY:',
                    '[%s] default source:%s' % (glottocode, source_string),
                    glottocode)

            elif not (source_string.find("p.c") == -1
                      and source_string.find("personal communication") == -1
                      and source_string.find("pers comm") == -1
                      and source_string.find("pers. comm") == -1
                      and source_string.find("ieldnotes") == -1
                      and source_string.find("ield notes") == -1
                      and source_string.find("forth") == -1
                      and source_string.find("Forth") == -1
                      and source_string.find("ubmitted") == -1
                      and source_string.find("o appear") == -1
                      and source_string.find("in press") == -1
                      and source_string.find("in prep") == -1
                      and source_string.find("in prog") == -1
                      and not source_string.startswith("http")):
                # FIXME: this variable is never read
                # I checked the pre-refactoring version.  Apparently
                # `src_comment` was passed out as a return value of the
                # `source_to_refs` function and then the caller (`bibdata`) just
                # threw away the value unused…
                # No idea what the original intent was -- maybe to add the
                # comment to row.Source_comment?
                src_comment = source_string

            elif authoryears:
                for author, year, pages, word_from_title in authoryears:
                    if (author, year, glottocode) in fixrefs:
                        matched_refs.append((fixrefs[(author, year, glottocode)], pages))
                    else:
                        unresolved_sources.append((author, year, glottocode))
            else:
                unresolved_sources.append((source_string, glottocode))

        if unresolved_sources:
            # FIXME mutating input data in-place
            row.Source_comment += ' (source not confirmed)'
            # FIXME mutating input data in-place
            unresolved.update(unresolved_sources)

        ### XXX: THIS IS THE CODE THAT DUMPS THE PARSED SOURCES FOR THIS ROW TO THE CALLER ###

        ref_pages = collections.OrderedDict()
        sources = []
        for bibkey, key_refs in groupby(matched_refs, lambda ref: ref[0]):
            typ, fields = bibliography_entries[bibkey]
            bibkey = clean_bibkey(bibkey)
            if bibkey not in ref_pages:
                ref_pages[bibkey] = set()
            ref_pages[bibkey].update(ref[1] for ref in key_refs if ref[1])
            sources.append(Source(typ, bibkey, **fields))

        # FIXME mutating input data in-place
        row.Source = [
            '{}{}'.format(ref, '[{}]'.format(','.join(sorted(pages))) if pages else '')
            for ref, pages in ref_pages.items()]
        for src in sources:
            yield src


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
