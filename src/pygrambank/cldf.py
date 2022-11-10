import re
import shutil
import pathlib
import collections

import pyglottolog
from clldutils.misc import lazyproperty, nfilter
from pycldf.dataset import GitRepository
from pycldf.sources import Source

from pygrambank import bib
from pygrambank import srctok
from pygrambank.sheet import Sheet
from pygrambank.contributors import PHOTO_URI, ROLES


def bibdata(sheet, values, e, lgks, unresolved):
    def clean_key(key):
        return key.replace(':', '_').replace("'", "")

    for row in values:
        if row.Source:
            row.Source_comment = row.Source
            refs, sources = collections.OrderedDict(), []
            uc = sum(list(unresolved.values()))
            res = srctok.source_to_refs(row.Source, sheet.glottocode, e, lgks, unresolved)
            if sum(list(unresolved.values())) > uc:  # pragma: no cover
                row.Source_comment += ' (source not confirmed)'
            for key, pages in res[0]:
                typ, fields = e[key]
                ref = key = clean_key(key)
                if ref not in refs:
                    refs[ref] = set()
                refs[ref] = refs[ref].union(pages or [])
                sources.append(Source(typ, key, **fields))

            row.Source = [
                '{}{}'.format(r, '[{}]'.format(','.join(sorted(p))) if p else '')
                for r, p in refs.items()]
            for src in sources:
                yield src


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


def refs(api, glottocode, bibs, lgks, sheet):
    def source(key):
        type_, fields = bibs[key]
        return key, type_, fields.get('author', fields.get('editor', '-')), fields.get('year', '-')

    unresolved = collections.Counter()
    res = bibdata(sheet, list(sheet.iter_row_objects(api)), bibs, lgks, unresolved)
    return list(res), unresolved, [source(k) for k in lgks[glottocode]]


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
