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


# XXX this is called by the cldfbench
def bibdata(sheet, values, bibliography_entries, bibkeys_by_glottocode, unresolved):
    def clean_key(key):
        return key.replace(':', '_').replace("'", "")

    for row in values:
        if not row.Source:
            continue

        # FIXME mutating input data in-place!!!
        row.Source_comment = row.Source
        refs, sources = collections.OrderedDict(), []
        uc = sum(list(unresolved.values()))

        source_string = row.Source
        glottocode = sheet.glottocode
        fixrefs = REFS
        authoryears = list(iter_authoryearpages(source_string))

        language_bibkeys = bibkeys_by_glottocode.get(glottocode, ())

        matched_refs = set()
        unmatched_refs = set()

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

            if not bibkeys and author_year_tuple not in unmatched_refs:
                print(colored('PARTIAL FAIL', color='red'))
                print('WARNING: unmatched reference: {}'.format(author_year_tuple))
                unmatched_refs.add(author_year_tuple)

        matched_refs = sorted(matched_refs, key=lambda r: (r[0], r[1] or ''))
        src_comment = None

        if not matched_refs:

            if REGEX_ONLY_PAGES.match(source_string):
                source_string = "[%s] default source:%s" % (glottocode, source_string)
                print("PAGEONLY:", source_string, glottocode)

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
                src_comment = source_string

            else:
                if authoryears:
                    for author, year, pages, word_from_title in authoryears:
                        if (author, year, glottocode) in fixrefs:
                            matched_refs.append((fixrefs[(author, year, glottocode)], pages))
                        else:
                            # FIXME mutating input data in-place
                            unresolved.update([(author, year, glottocode)])
                else:
                    # FIXME mutating input data in-place
                    unresolved.update([(source_string, glottocode)])

        res = (
            [(k, [r[1] for r in rs if r[1]])
             for k, rs in groupby(matched_refs, lambda r: r[0])],
            src_comment)

        if sum(list(unresolved.values())) > uc:  # pragma: no cover
            # FIXME mutating input data in-place
            row.Source_comment += ' (source not confirmed)'
        for key, pages in res[0]:
            typ, fields = bibliography_entries[key]
            ref = key = clean_key(key)
            if ref not in refs:
                refs[ref] = set()
            refs[ref] = refs[ref].union(pages or [])
            sources.append(Source(typ, key, **fields))

        # FIXME mutating input data in-place
        row.Source = [
            '{}{}'.format(r, '[{}]'.format(','.join(sorted(p))) if p else '')
            for r, p in refs.items()]
        for src in sources:
            yield src


# XXX this is called by the cldfbench
# (mostly to be fed into `bibdata`)
class Bibs(dict):
    def __init__(self, glottolog, api):
        dict.__init__(self, glottolog.bib('hh'))
        self.update(api.bib)

    def iter_codes(self):
        for key, (typ, fields) in self.items():
            if 'lgcode' in fields:
                for code in bib.lgcodestr(fields['lgcode']):
                    yield key, code


def languoid_id_map(glottolog, glottocodes):
    id_map = {}

    for glottocode in glottocodes:
        languoid = glottolog.api.languoid(glottocode)
        lang = None

        # Determine the associated language-level languoid:
        if languoid.level.name == 'dialect':  # pragma: no cover
            for _, gc, _ in reversed(languoid.lineage):
                lang = glottolog.api.languoid(gc)
                if lang.level.name == 'language':
                    break
        else:
            lang = languoid

        potential_ids = [
            languoid.id, languoid.hid, languoid.iso, lang.id, lang.hid, lang.iso]
        id_map.update((id_, glottocode) for id_ in potential_ids if id_)

    return id_map


def refs(api, glottocode, bibs, bibkeys_by_glottocode, sheet):
    def source(key):
        type_, fields = bibs[key]
        return key, type_, fields.get('author', fields.get('editor', '-')), fields.get('year', '-')

    unresolved = collections.Counter()
    res = bibdata(sheet, list(sheet.iter_row_objects(api)), bibs, bibkeys_by_glottocode, unresolved)
    return list(res), unresolved, [source(k) for k in bibkeys_by_glottocode[glottocode]]


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
