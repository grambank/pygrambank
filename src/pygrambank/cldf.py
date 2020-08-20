import pathlib
import collections

import pyglottolog
from clldutils.misc import lazyproperty, nfilter
from pycldf import StructureDataset
from pycldf.dataset import GitRepository
from pycldf.sources import Source

from pygrambank import bib
from pygrambank import srctok
from pygrambank.sheet import Sheet
from pygrambank.util import iterunique

# FIXME: These should be fixed in the data!
INVALID = ['9', '.?']


def bibdata(sheet, values, e, lgks, unresolved):
    def clean_key(key):
        return key.replace(':', '_').replace("'", "")

    for row in values:
        if row.Source:
            row.Source_comment = row.Source
            refs, sources = [], []
            res = srctok.source_to_refs(row.Source, sheet.glottocode, e, lgks, unresolved)
            for key, pages in res[0]:
                typ, fields = e[key]
                ref = key = clean_key(key)
                if pages:
                    ref += '[{0}]'.format(','.join(pages))
                refs.append(ref)
                sources.append(Source(typ, key, **fields))

            row.Source = refs
            for src in sources:
                yield src


def refs(api, glottolog, sheet):
    glottolog = Glottolog(glottolog)
    languoid, lang = glottolog.api.languoid(sheet.glottocode), None

    # Determine the associated language-level languoid:
    if languoid.level.name == 'dialect':
        for _, gc, _ in reversed(languoid.lineage):
            lang = glottolog.api.languoid(gc)
            if lang.level.name == 'language':
                break
    else:
        lang = languoid

    ids = set(nfilter([languoid.id, languoid.hid, languoid.iso, lang.id, lang.hid, lang.iso]))

    bibs = glottolog.bib('hh')
    bibs.update(api.bib)

    lgks = collections.defaultdict(set)
    for key, (typ, fields) in bibs.items():
        if 'lgcode' in fields:
            for code in bib.lgcodestr(fields['lgcode']):
                if code in ids:
                    lgks[languoid.id].add(key)

    def source(key):
        type_, fields = bibs[key]
        return key, type_, fields.get('author', fields.get('editor', '-')), fields.get('year', '-')

    unresolved = collections.Counter()
    res = bibdata(sheet, list(sheet.iter_row_objects(api)), bibs, lgks, unresolved)
    return list(res), unresolved, [source(k) for k in lgks[languoid.id]]


def create(api, glottolog, wiki, cldf_repos):
    glottolog = Glottolog(glottolog)
    sheets = [
        Sheet(f) for f in sorted(api.sheets_dir.glob('*.tsv'), key=lambda p: p.stem)]
    sheets = [(s, list(s.iter_row_objects(api))) for s in sheets]

    # Chose best sheet for indivdual Glottocodes:
    print('selecting best sheets')
    sheets = list(iterunique(sheets, verbose=True))

    descendants = glottolog.descendants_map

    print('loading bibs')
    bibs = glottolog.bib('hh')
    bibs.update(api.bib)

    print('computing lang-to-refs mapping ...')
    lgks = collections.defaultdict(set)
    for key, (typ, fields) in bibs.items():
        if 'lgcode' in fields:
            for code in bib.lgcodestr(fields['lgcode']):
                if code in glottolog.languoids_by_ids:
                    gc = glottolog.languoids_by_ids[code].id
                    if gc in descendants:
                        for cl in descendants[gc]:
                            lgks[cl].add(key)
                    else:
                        print('---non-language', code)
    print('... done')

    dataset = StructureDataset.in_dir(cldf_repos / 'cldf')
    dataset.add_provenance(
        wasDerivedFrom=[
            GitRepository('https://github.com/glottobank/Grambank', clone=api.repos),
            GitRepository('https://github.com/glottolog/glottolog', clone=glottolog.api.repos),
            GitRepository('https://github.com/glottobank/Grambank/wiki', clone=wiki),
        ],
        wasGeneratedBy=GitRepository(
            'https://github.com/glottobank/pygrambank',
            clone=pathlib.Path(__file__).parent.parent.parent),
    )
    create_schema(dataset)

    data, families = collections.defaultdict(list), set()

    for fid, feature in sorted(api.features.items()):
        data['ParameterTable'].append(dict(
            ID=fid,
            Name=feature.name,
            Description=feature.description,
            patron=feature.patron,
            name_in_french=feature.name_french,
            Grambank_ID_desc=feature['Grambank_ID_desc'],
            bound_morphology=feature['bound_morphology']
        ))
        for code, desc in sorted(feature.domain.items(), key=lambda i: int(i[0])):
            data['CodeTable'].append(dict(
                ID='{0}-{1}'.format(fid, code),
                Parameter_ID=fid,
                Name=code,
                Description=desc,
            ))

    data['contributors.csv'] = [dict(ID=c.id, Name=c.name) for c in api.contributors]
    cids = set(d['ID'] for d in data['contributors.csv'])

    def coders(sheet, row):
        return sorted(set(sheet.coders).union(row.contributed_datapoint))

    unresolved, coded_sheets = collections.Counter(), {}
    for sheet, values in sorted(sheets, key=lambda i: i[0].glottocode):
        if not values:  # pragma: no cover
            print('ERROR: empty sheet {0}'.format(sheet.path))
            continue
        lang = glottolog.languoids_by_glottocode[sheet.glottocode]
        coded_sheets[sheet.glottocode] = sheet
        for c in sheet.coders:
            if c not in cids:
                raise ValueError('unknown coder ID: {0} in {1}'.format(c, sheet.path))
        ld = dict(
            ID=sheet.glottocode,
            Name=lang.name,
            Glottocode=sheet.glottocode,
            Coders=sheet.coders,
            provenance=sheet.path.name,
        )
        ld.update(sheet.metadata(glottolog))
        data['LanguageTable'].append(ld)
        if ld['Family_id']:
            families.add(ld['Family_id'])
        dataset.add_sources(*list(bibdata(sheet, values, bibs, lgks, unresolved)))
        for row in sorted(values, key=lambda r: r.Feature_ID):
            if row.Value in INVALID:
                continue
            data['ValueTable'].append(dict(
                ID='{0}-{1}'.format(row.Feature_ID, sheet.glottocode),
                Language_ID=sheet.glottocode,
                Parameter_ID=row.Feature_ID,
                Code_ID='{0}-{1}'.format(row.Feature_ID, row.Value) if row.Value != '?' else None,
                Value=row.Value,
                Comment=row.Comment,
                Source=row.Source,
                Source_comment=row.Source_comment,
                Coders=coders(sheet, row),
            ))

    print('computing newick trees')
    data['families.csv'] = sorted([
        {
            'ID': gc,
            'Newick': glottolog.api.newick_tree(
                gc, template='{l.id}', nodes=glottolog.languoids_by_glottocode),
        } for gc in families], key=lambda d: d['ID'])
    dataset.write(**data)

    per_sheet = collections.defaultdict(list)
    for k, v in reversed(unresolved.most_common()):
        print(k, v)
        per_sheet[k[-1]].append(k[:-1])
    print(sum(unresolved.values()))

    return coded_sheets


class Glottolog(object):
    """
    A custom facade to the Glottolog API.
    """
    def __init__(self, repos):
        self.api = pyglottolog.Glottolog(repos)

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
        return {l.id: l for l in self.languoids}

    @lazyproperty
    def descendants_map(self):
        res = collections.defaultdict(list)
        for l in self.languoids:
            res[l.id].append(l.id)
            if l.lineage:
                for _, gc, _ in l.lineage:
                    res[gc].append(l.id)
        return res

    @lazyproperty
    def languoids_by_ids(self):
        """
        We provide a simple lookup for the three types of identifiers for a Glottolog languoid,
        where hid takes precedence over ISO 639-3 code.
        """
        res = {}
        for l in self.languoids:
            res[l.id] = l
            if l.iso:
                res[l.iso] = l
        for l in self.languoids:
            if l.hid:
                res[l.hid] = l
        return res


def create_schema(dataset):
    dataset.add_table('contributors.csv', 'ID', 'Name')

    table = dataset.add_component(
        'LanguageTable',
        {
            'name': 'Coders',
            'dc:description': 'the contributor of the codings for this language',
            'separator': ';',
        },
        {
            'name': 'provenance',
            'dc:description': 'name and last modification of the contributed file',
        },
        'Family_name',
        'Family_id',
        'Language_id',
        'level',
        {
            'name': 'lineage',
            'separator': '/',
            'dc:description': 'list of ancestor groups in the Glottolog classification',
        },
    )
    table.add_foreign_key('Family_id', 'families.csv', 'ID')
    table.add_foreign_key('Coders', 'contributors.csv', 'ID')

    dataset.add_component(
        'ParameterTable',
        {
            'name': 'patron',
            'dc:description': 'Grambank editor responsible for this feature',
        },
        'name_in_french',
        'Grambank_ID_desc',
        'bound_morphology',
    )
    dataset.add_component('CodeTable')
    dataset.add_columns('ValueTable', 'Source_comment', {"name": "Coders", "separator": ";"})
    dataset['ValueTable', 'Value'].null = ['?']
    dataset['ValueTable'].add_foreign_key('Coders', 'contributors.csv', 'ID')

    table = dataset.add_table('families.csv', 'ID', 'Newick')
    table.common_props['dc:conformsTo'] = None
    table.tableSchema.primaryKey = ['ID']
