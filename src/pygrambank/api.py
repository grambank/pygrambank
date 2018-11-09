from __future__ import unicode_literals
import re

from openpyxl import load_workbook

from clldutils.apilib import API
from clldutils.misc import lazyproperty
from clldutils.path import read_text
from pyglottolog.references.bibfiles import BibFile


class Feature(object):
    def __init__(self, spec, wiki):
        self._spec = spec
        self._wiki = wiki
        self.domain = {}
        spec = self._spec['Possible Values'].replace('multistate', '').strip()
        delimiter = ',' if ',' in spec else ';'
        for val in spec.split(delimiter):
            val, desc = re.split('\s*:\s*', val.strip())
            int(val)
            self.domain[val] = desc

    @lazyproperty
    def description(self):
        if self._wiki.joinpath('{0}.md'.format(self.id)).exists():
            return read_text(self._wiki.joinpath('{0}.md'.format(self.id)))
        return self._spec['Clarifying Comments']

    @lazyproperty
    def id(self):
        return self._spec['Grambank ID']

    @lazyproperty
    def name(self):
        return self._spec['Feature']

    @lazyproperty
    def patron(self):
        return self._spec['Feature patron']


class Grambank(API):
    def __init__(self, repos, wiki=None):
        API.__init__(self, repos)
        self.wiki = wiki or self.repos.parent / 'Grambank.wiki'

    @property
    def sheets_dir(self):
        return self.repos / 'original_sheets'

    @lazyproperty
    def bib(self):
        return {e.key: (e.type, e.fields) for e in BibFile(self.repos / 'gb.bib').iterentries()}

    @lazyproperty
    def features(self):
        sheet = load_workbook(
            str(self.path('For_coders', 'GramBank_most_updated_sheet.xlsx')), data_only=True).active
        rows = [[col.value for col in row] for row in sheet.rows]
        return {
            f['Grambank ID']: Feature(f, self.wiki)
            for f in [dict(zip(rows[0], row)) for row in rows[1:]]}
