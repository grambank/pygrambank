from __future__ import unicode_literals

from clldutils.apilib import API
from clldutils.misc import lazyproperty
from pyglottolog.references.bibfiles import BibFile

from pygrambank.features import GB20
from pygrambank.contributors import Contributors


class Grambank(API):
    def __init__(self, repos, wiki=None):
        API.__init__(self, repos)
        self.wiki = wiki or self.repos.parent / 'Grambank.wiki'
        self.gb20 = GB20(self.path('gb20.txt'))

    @property
    def sheets_dir(self):
        return self.repos / 'original_sheets'

    @property
    def contributors(self):
        return Contributors.from_md(self.repos / 'CONTRIBUTORS.md')

    @lazyproperty
    def bib(self):
        return {e.key: (e.type, e.fields) for e in BibFile(self.repos / 'gb.bib').iterentries()}

    @lazyproperty
    def ordered_features(self):
        return list(self.gb20.iterfeatures(self.wiki))

    @lazyproperty
    def features(self):
        return {f['Grambank ID']: f for f in self.ordered_features}

    def visit_feature(self, visitor):
        features = []
        for f in self.ordered_features:
            f = visitor(f, self)
            if f:
                features.append(f)
        self.gb20.save(features)
